import io
import os
import re
import pandas as pd
from flask import request, jsonify, send_file, Blueprint
from datetime import datetime, time

transform_bp = Blueprint('transform', __name__)

KNOWN_HEADER_KEYWORDS = {
    'subject', 'protocol', 'randomization', 'visit', 'collection', 'sample',
    'analyte', 'screen', 'box', 'comment', 'type', 'id', 'time', 'day'
}

def normalize_cell(cell):
    return str(cell).lower().strip() \
        .replace('\n', ' ').replace('\r', '') \
        .replace('\t', ' ').replace('  ', ' ')

def find_data_block(df):
    best_start = None
    best_score = 0
    for i in range(len(df)):
        filled_rows = 0
        for j in range(i, min(i + 10, len(df))):
            if df.iloc[j].notna().sum() >= 4:
                filled_rows += 1
        if filled_rows >= 5 and filled_rows > best_score:
            best_score = filled_rows
            best_start = i
    return best_start

def find_header_within_block(df, start_index, look_back=5, look_forward=10):
    best_row = None
    best_matches = 0
    start = max(0, start_index - look_back)
    end = min(len(df), start_index + look_forward)
    for i in range(start, end):
        row = df.iloc[i].dropna().map(normalize_cell)
        matches = sum(any(kw in cell for kw in KNOWN_HEADER_KEYWORDS) for cell in row)
        if matches > best_matches:
            best_matches = matches
            best_row = i
    return best_row

def find_fallback_header_row(df, start_index):
    for i in range(start_index, len(df)):
        if df.iloc[i].notna().sum() >= 3:
            return i
    return start_index

def standardize_datetime(val):
    if pd.isna(val):
        return ''

    s = str(val).strip()

    # special-case bare YYYYMMDD
    if len(s) == 8 and s.isdigit():
        try:
            return datetime.strptime(s, '%Y%m%d').date().isoformat()
        except ValueError:
            # fall through to general parsing
            pass

    # flexible parse (use dayfirst=True if your locale is D/M/Y)
    parsed = pd.to_datetime(s, dayfirst=True, errors='coerce')
    if pd.isna(parsed):
        return s  # keep protocol numbers, etc.

    # time-only values: pandas sets date to 1970-01-01
    if parsed.time() != time.min and parsed.date() == datetime(1970, 1, 1).date():
        return parsed.strftime('%H:%M:%S')
    # pure dates (no time component)
    elif parsed.time() == time.min:
        return parsed.strftime('%Y-%m-%d')
    # mixed datetime (date+time) — keep original string
    else:
        return s


def handle_column_time_and_date(df):
    """
    Apply standardize_datetime only to columns whose
    names suggest they contain dates or times.
    """
    def is_date_col(col):
        low = col.lower()
        return any(kw in low for kw in ('date', 'time', 'day', 'visit'))

    for col in df.columns:
        if is_date_col(col):
            df[col] = df[col].apply(standardize_datetime)
    return df

@transform_bp.route('/analyze-columns', methods=['POST'])
def analyze_columns():
    file = request.files['file']
    ext = file.filename.rsplit('.', 1)[-1].lower()

    try:
        raw = (pd.read_excel(file, header=None, dtype=str)
               if 'xls' in ext else pd.read_csv(file, header=None, dtype=str))
    except Exception as e:
        return jsonify({'error': f'File read failed: {e}'}), 400

    data_start = find_data_block(raw)
    if data_start is None:
        return jsonify({'error': 'No data block found'}), 400

    header_row = find_header_within_block(raw, data_start, look_back=5, look_forward=10)
    if header_row is None:
        header_row = find_fallback_header_row(raw, data_start)

    file.seek(0)
    df = (pd.read_excel(file, header=header_row, dtype=str)
          if 'xls' in ext else pd.read_csv(file, header=header_row, dtype=str))

    df = df.dropna(how='all')
    df.columns = df.columns.str.replace(r'\s*\n\s*', ' ', regex=True).str.strip()

    return jsonify({'columns': df.columns.tolist(), 'rows': len(df)}), 200

@transform_bp.route('/generate-manifest', methods=['POST', 'OPTIONS'])
def generate_manifest():
    if request.method == 'OPTIONS':
        return '', 200

    file = request.files['file']
    config = request.form.to_dict(flat=False)
    output_format = request.form.get('format', 'excel')
    ext = file.filename.rsplit('.', 1)[-1].lower()

    try:
        raw = (pd.read_excel(file, header=None, dtype=str)
               if 'xls' in ext else pd.read_csv(file, header=None, dtype=str))
    except Exception as e:
        return jsonify({'error': f'File read failed: {e}'}), 400

    data_start = find_data_block(raw)
    if data_start is None:
        return jsonify({'error': 'No data block found'}), 400

    header_row = find_header_within_block(raw, data_start, look_back=5, look_forward=10)
    if header_row is None:
        header_row = find_fallback_header_row(raw, data_start)

    file.seek(0)
    df = (pd.read_excel(file, header=header_row, dtype=str)
          if 'xls' in ext else pd.read_csv(file, header=header_row, dtype=str))

    df = df.dropna(how='all').fillna('')
    df.columns = df.columns.str.replace(r'\s*\n\s*', ' ', regex=True).str.strip()
    df = handle_column_time_and_date(df)

    final = pd.DataFrame()
    col_map = {
        'PRODUCT ID':      config.get('PRODUCT ID', [None])[0],
        'PRODUCT VERSION': config.get('PRODUCT VERSION', [None])[0],
        'SUBJECT ID':      config.get('SUBJECT ID', [None])[0],
        'MERCODIA ID':     config.get('MERCODIA ID', [None])[0],
    }

    for col in ['PRODUCT ID', 'PRODUCT VERSION', 'SUBJECT ID']:
        src = col_map[col]
        final[col] = df[src] if src and src in df.columns else ''

    optionals = config.get('OPTIONAL', [])
    customs = config.get('CUSTOM', [])
    header_names = []

    for i in range(11):
        original = optionals[i] if i < len(optionals) else ''
        if original == 'CUSTOM':
            header = customs[i] if i < len(customs) else ''
            series = pd.Series([''] * len(df))
        elif original:
            match = next((col for col in df.columns 
                          if col.replace('\n',' ').strip().lower() == original.replace('\n',' ').strip().lower()), None)
            if match:
                header = match
                series = df[match]
            else:
                header = original
                series = pd.Series([''] * len(df))
        else:
            header = ''
            series = pd.Series([''] * len(df))
        final[header] = series
        header_names.append(header)

    src = col_map['MERCODIA ID']
    if src and src in df.columns:
        final['MERCODIA ID'] = df[src]
    else:
        final['MERCODIA ID'] = pd.Series([''] * len(df))

    cols_ordered = ['PRODUCT ID', 'PRODUCT VERSION', 'SUBJECT ID'] + header_names + ['MERCODIA ID']
    final = final[cols_ordered]

    project = request.form.get('Project ID', '')
    subproject = request.form.get('Subproject ID', '')
    request_id = request.form.get('Request ID', '')

    top_rows = pd.DataFrame([
        ['Project ID', project],
        ['Subproject ID', subproject],
        ['Request ID', request_id],
        []
    ])

    buffer = io.BytesIO()
    if output_format == 'csv':
        top_rows.to_csv(buffer, index=False, header=False)
        final.to_csv(buffer, index=False)
    else:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            top_rows.to_excel(writer, index=False, header=False, startrow=0)
            final.to_excel(writer, index=False, startrow=4)

    buffer.seek(0)
    original_name = os.path.splitext(file.filename)[0]
    ext_out = "xlsx" if output_format == "excel" else "csv"
    fname = f'LIMS_{original_name}.{ext_out}'
    return send_file(buffer, as_attachment=True, download_name=fname)

@transform_bp.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
    return response

@transform_bp.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 204