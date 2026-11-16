import pandas as pd
import re
from flask import Blueprint, request, jsonify
from datetime import datetime, time

review_bp = Blueprint('review', __name__)

PLACEHOLDER_VALUES = {'n/a', '-', '', 'na', 'null'}
REQUIRED_FIELDS = ['PRODUCT ID', 'PRODUCT VERSION', 'SUBJECT ID', 'MERCODIA ID']
METADATA_KEYWORDS = ['request', 'report', 'page', 'generated', 'customer']

def normalize_cell(cell):
    return str(cell).lower().strip()

def normalize_columns(df):
    def normalize(text):
        return re.sub(r'[^A-Z0-9]', '', str(text).strip().upper())
    df.columns = [normalize(col) for col in df.columns]
    return df


def normalize_placeholder(value):
    val = str(value).strip().lower()
    return '' if val in PLACEHOLDER_VALUES else val

def find_data_block(df, min_filled=0.6, window_size=10, required_rows=5):
    """
    Find the index of the first row in the actual data block (ignores metadata).
    Looks for a window of rows that are mostly filled.
    """
    n_cols = df.shape[1]
    min_filled_cells = int(n_cols * min_filled)

    best_start = None
    best_score = 0

    for i in range(len(df) - window_size):
        filled_rows = 0
        for j in range(window_size):
            row = df.iloc[i + j]
            non_empty = row.dropna().astype(str).str.strip()
            if len(non_empty) >= min_filled_cells:
                filled_rows += 1
        if filled_rows >= required_rows:
            return i  # found a dense-enough block
    return 0  # fallback if none found

def get_flexible_column(df, name):
    norm_target = re.sub(r'[^A-Z0-9]', '', str(name).strip().upper())
    # Exact match
    for col in df.columns:
        if col == norm_target:
            return col
    # Partial match fallback
    for col in df.columns:
        if norm_target in col or col in norm_target:
            return col
    return None


def find_header_within_block(df, start_index=None, look_back=5, look_forward=30):
    """
    Detect header row by looking for rows that:
    - Are not metadata (e.g. 'Customer Report', 'Generated')
    - Contain multiple known header keywords like 'SUBJECT ID'
    - Have more than 1 non-empty cell
    """
    REQUIRED_KEYWORDS = ['SUBJECT ID', 'COLLECTION DATE', 'SAMPLE TYPE', 'VISIT', 'TIME POINT']
    METADATA_KEYWORDS = ['report', 'generated', 'customer', 'page', 'request', 'created', 'date']

    search_range = range(
        max(0, (start_index or 0) - look_back),
        min(len(df), (start_index or 0) + look_forward)
    )

    for i in search_range:
        row = df.iloc[i].dropna().astype(str).str.upper().str.strip()
        if len(row) <= 1:
            continue  # skip rows with 0 or 1 filled cells

        combined = ' '.join(row)
        if any(meta in combined for meta in METADATA_KEYWORDS):
            continue  # skip metadata lines

        match_count = sum(any(req in cell for req in REQUIRED_KEYWORDS) for cell in row)
        if match_count >= 2:
            return i

    # Fallback if nothing better found
    return 0


def is_data_row(row):
    non_empty = row.dropna().astype(str).str.strip()
    if len(non_empty) <= 1:
        return False
    combined = ' '.join(non_empty).lower()
    if any(kw in combined for kw in METADATA_KEYWORDS):
        return False
    has_number_or_date = any(re.search(r'\d', cell) for cell in non_empty)
    return has_number_or_date or len(non_empty) >= 2

def standardize_dates(df):
    time_pattern = re.compile(r'^\d{1,2}:\d{2}(?::\d{2})?$')
    date_formats = ['%d.%m.%Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']

    def parse_individual(val):
        # handle NaN/empty
        if pd.isna(val) or str(val).strip() == '':
            return ''
        s = str(val).strip()

        # bare YYYYMMDD
        if len(s) == 8 and s.isdigit():
            try:
                return datetime.strptime(s, '%Y%m%d').date().isoformat()
            except ValueError:
                pass

        # generic parse
        parsed = pd.to_datetime(s, dayfirst=True, errors='coerce')
        if pd.isna(parsed):
            # keep non-dates intact
            return s

        # time-only (pandas uses 1970-01-01)
        if parsed.date() == datetime(1970, 1, 1).date() and parsed.time() != time.min:
            return parsed.strftime('%H:%M:%S')
        # pure date (midnight)
        if parsed.time() == time.min:
            return parsed.strftime('%Y-%m-%d')
        # mixed datetime → leave as original
        return s

    for col in df.columns:
        try:
            series = df[col].astype(str).str.strip()
            non_empty = series[series != '']
            # If >80% of values match a time-only pattern, skip this column
            if len(non_empty) > 0 and (non_empty.str.match(time_pattern).sum() / len(non_empty)) > 0.8:
                continue

            # Try explicit formats first
            for fmt in date_formats:
                converted = pd.to_datetime(series, format=fmt, errors='coerce')
                good = converted.notna().sum()
                if good > 0.8 * len(series) and not (converted.dt.year == 1970).all():
                    df[col] = converted.dt.strftime('%Y-%m-%d')
                    break
            else:
                # Fallback generic parse if not all 1970
                converted = pd.to_datetime(series, errors='coerce', dayfirst=True)
                if converted.notna().sum() > 0 and not (converted.dt.year == 1970).all():
                    df[col] = converted.dt.strftime('%Y-%m-%d')
                else:
                    # Apply cell‐by‐cell for times, bare YYYYMMDD, or keep originals
                    df[col] = df[col].apply(parse_individual)
        except Exception:
            # on any error, leave column as-is
            continue

    return df


@review_bp.route('/review', methods=['POST'])
def review_excel():
    if 'manifest' not in request.files or 'report' not in request.files:
        return jsonify({'status': 'fail', 'issues': ['Both manifest and report files are required.']}), 400

    manifest_file = request.files['manifest']
    report_file = request.files['report']

    ext1 = manifest_file.filename.rsplit('.', 1)[-1].lower()
    ext2 = report_file.filename.rsplit('.', 1)[-1].lower()

    try:
        if 'csv' in ext1:
            manifest_raw = pd.read_csv(manifest_file, header=None, dtype=str)
        else:
            manifest_raw = pd.read_excel(manifest_file, header=None, dtype=str)
        if 'csv' in ext2:
            report_raw = pd.read_csv(report_file, header=None, dtype=str)
        else:
            report_raw = pd.read_excel(report_file, header=None, dtype=str)
    except Exception as e:
        return jsonify({'status': 'fail', 'issues': [f'Failed to read input files: {str(e)}']}), 400

    start1 = find_data_block(manifest_raw)
    header1 = find_header_within_block(manifest_raw, start1)

    start2 = find_data_block(report_raw)
    try:
        header2 = find_header_within_block(report_raw, start2)
    except ValueError as e:
        return jsonify({'status': 'fail', 'issues': [str(e)]}), 400

    manifest_file.seek(0)
    report_file.seek(0)

    try:
        if 'csv' in ext1:
            manifest = pd.read_csv(manifest_file, header=header1, dtype=str).fillna('')
        else:
            manifest = pd.read_excel(manifest_file, header=header1, dtype=str).fillna('')
    except Exception as e:
        return jsonify({'status': 'fail', 'issues': [f'Failed to parse manifest file: {str(e)}']}), 400

    try:
        if 'csv' in ext2:
            report = pd.read_csv(report_file, header=header2, dtype=str).fillna('')
        else:
            report = pd.read_excel(report_file, header=header2, dtype=str).fillna('')
    except Exception as e:
        return jsonify({'status': 'fail', 'issues': [f'Failed to parse report file: {str(e)}']}), 400

    manifest.columns = (
        manifest.columns
                .astype(str)      # ensure they're strings
                .str.strip()      # remove leading/trailing whitespace
                .str.upper()      # normalize to uppercase
    )
    # 1) Drop columns whose name is empty (otional: number)
    manifest = manifest.loc[
        :, 
        ~manifest.columns.str.match(r'(?i)^Unnamed:\s*\d+')
    ]


    print("DEBUG - Manifest Columns:", manifest.columns.tolist())
    print("DEBUG - Report Columns:", report.columns.tolist())

    manifest = standardize_dates(manifest)
    report = standardize_dates(report)

    manifest = manifest[manifest.apply(is_data_row, axis=1)].reset_index(drop=True)
    report = report[report.apply(is_data_row, axis=1)].reset_index(drop=True)

    correct_parts = []
    issues = []

    # Step 1: Sample count
    if len(manifest) == len(report):
        correct_parts.append(f'Sample count matches: {len(manifest)} samples')
    else:
        issues.append(f'Sample count mismatch: Manifest={len(manifest)}, Report={len(report)}')

    # Step 2: Required columns
    required_manifest_only = ['PRODUCT ID', 'PRODUCT VERSION', 'MERCODIA ID']
    required_both = ['SUBJECT ID']

    missing_manifest = [c for c in required_manifest_only if c not in manifest.columns]
    missing_both = [c for c in required_both if c not in manifest.columns or c not in report.columns]

    if not missing_manifest and not missing_both:
        correct_parts.append('All required columns are present')
    else:
        if missing_manifest:
            issues.append(f"Missing required column(s) in Sample Manifest: {', '.join(missing_manifest)}")
        if missing_both:
            issues.append(f"Missing required column(s) in both files: {', '.join(missing_both)}")

    # Step 2.5: Forbidden columns in report
    forbidden_in_report = ['PRODUCT ID', 'PRODUCT VERSION', 'MERCODIA ID']
    for col in forbidden_in_report:
        if col in report.columns:
            issues.append(f"Column '{col}' should not be present in the Customer Report")

    # Step 3: Compare sample data
    forbidden_cols = set(forbidden_in_report)
    allowed_compare_cols = [
        col for col in manifest.columns
        if col not in forbidden_cols and col not in required_manifest_only
    ]

    min_len = min(len(manifest), len(report))
    row_mismatches = []
    missing_cols = []

    for col in allowed_compare_cols:
        if col not in report.columns:
            issues.append(f"Optional column '{col}' is missing in the Customer Report.")
            missing_cols.append(col)
            continue

        for i in range(min_len):
            val1 = normalize_placeholder(manifest[col].iloc[i])
            val2 = normalize_placeholder(report[col].iloc[i])
            if val1 != val2:
                mismatch_msg = f"Row {i+1}, column '{col}': Expected '{val1 or '[blank]'}', found '{val2 or '[blank]'}'"
                issues.append(mismatch_msg)
                row_mismatches.append(mismatch_msg)

    # Step 4: Only add match message if nothing was skipped or mismatched
    if not row_mismatches and not missing_cols:
        correct_parts.append("All sample data match across files")

    response = {
        'status': 'pass' if not issues else 'fail',
        'summary': correct_parts,
        'issues': issues,
        'sampleCount': len(manifest),
        'detected_rows': {'manifest_start': start1, 'report_start': start2}
    }

    return jsonify(response)

def detect_qaqc_header_row(df, min_filled=0.6, window_size=10, required_rows=5):
    header_keywords = [
        'SAMPLE ALIAS', 'SUBJECT ID', 'CALCULATED CONCENTRATION',
        'CV (%)', 'APPROVAL STATUS', 'PLATE APPROVAL STATUS'
    ]
    metadata_keywords = ['report', 'generated', 'customer', 'page', 'request', 'created', 'date', 'study', 'method', 'product']

    best_index = 0
    best_score = 0

    for i in range(len(df)):
        row = df.iloc[i].dropna().astype(str).str.upper().str.strip()
        if any(any(meta in cell.lower() for meta in metadata_keywords) for cell in row):
            continue

        score = sum(any(key in cell for key in header_keywords) for cell in row)
        if score > best_score:
            best_index = i
            best_score = score

    print(f"DEBUG: Best header match for QAQC at row {best_index}")
    return best_index

def is_data_row(row):
    non_empty = row.dropna().astype(str).str.strip()
    if len(non_empty) <= 1:
        return False
    combined = ' '.join(non_empty).lower()
    if any(kw in combined for kw in ['request', 'report', 'page', 'generated', 'customer']):
        return False
    return True

@review_bp.route('/review-qaqc', methods=['POST'])
def review_qaqc():
    summary = []
    issues = []
    status = 'pass'

    if 'customer' not in request.files or 'qaqc' not in request.files:
        issues.append("Missing one or both required files in the request.")
        return jsonify({'status': 'fail', 'summary': summary, 'issues': issues})

    customer_file = request.files['customer']
    qaqc_file = request.files['qaqc']
    
    ext_cust = customer_file.filename.rsplit('.', 1)[-1].lower()
    ext_qa   = qaqc_file.   filename.rsplit('.', 1)[-1].lower()

    try:
        # read customer file
        if ext_cust == 'csv':
            customer_raw = pd.read_csv(customer_file, header=None, dtype=str)
        else:
            customer_raw = pd.read_excel(customer_file, header=None, dtype=str)

        # read QA/QC file
        if ext_qa == 'csv':
            qaqc_raw = pd.read_csv(qaqc_file, header=None, dtype=str)
        else:
            qaqc_raw = pd.read_excel(qaqc_file, header=None, dtype=str)
    except Exception as e:
        issues.append(f"File read error: {e}")
        return jsonify({ 'status': 'error', 'summary': summary, 'issues': issues })


    # drop completely blank rows
    customer_raw = customer_raw.dropna(how='all').reset_index(drop=True)
    qaqc_raw    = qaqc_raw.dropna(how='all').reset_index(drop=True)

    # detect headers
    cust_header = find_header_within_block(customer_raw, find_data_block(customer_raw))
    qaqc_header = detect_qaqc_header_row(qaqc_raw)

    try:
        # slice out data under the headers
        customer_df = customer_raw.iloc[cust_header + 1:].reset_index(drop=True)
        customer_df.columns = customer_raw.iloc[cust_header].tolist()
        customer_df = customer_df.fillna('')

        qaqc_df = qaqc_raw.iloc[qaqc_header + 1:].reset_index(drop=True)
        qaqc_df.columns = qaqc_raw.iloc[qaqc_header].tolist()
        qaqc_df = qaqc_df.fillna('')

        print("DEBUG - QAQC Columns:", list(qaqc_df.columns))
    except Exception as e:
        issues.append(f"Excel parsing error: {e}")
        return jsonify({'status': 'fail', 'summary': summary, 'issues': issues})

    # normalize names
    def norm_cols(cols):
        return [
            str(c).strip().upper()
                .replace('(%)', '%')
                .replace('(', '').replace(')', '')
                .replace(' %', '%')
            for c in cols
        ]

    customer_df.columns = norm_cols(customer_df.columns)
    qaqc_df.columns     = norm_cols(qaqc_df.columns)

    # remove metadata rows
    customer_df = customer_df[customer_df.apply(is_data_row, axis=1)].reset_index(drop=True)
    qaqc_df     = qaqc_df[qaqc_df.apply(is_data_row, axis=1)].reset_index(drop=True)

    # Step 1: must have both status columns
    if 'APPROVAL STATUS' not in qaqc_df.columns or 'PLATE APPROVAL STATUS' not in qaqc_df.columns:
        issues.append("QA/QC Report is missing the required 'APPROVAL STATUS' or 'PLATE APPROVAL STATUS' column.")
        return jsonify({'status': 'fail', 'summary': summary, 'issues': issues})

    # ————— only abort if PLATE=FAIL but SAMPLE=PASS —————
    inconsistent = (
        (qaqc_df['PLATE APPROVAL STATUS'].str.upper() == 'FAIL')
        & (qaqc_df['APPROVAL STATUS'].str.upper() == 'PASS')
    )
    if inconsistent.any():
        bad_rows = (inconsistent[inconsistent].index + qaqc_header + 1).tolist()
        issues.append(
            f"Inconsistent statuses at QA/QC row(s) {bad_rows}: "
            "PLATE APPROVAL='FAIL' but APPROVAL STATUS='PASS'."
        )
        return jsonify({'status': 'fail', 'summary': [], 'issues': issues})

    # ————— now drop *all* non-PASS rows (both plate- and sample-FAILs) —————
    pass_mask = (
        (qaqc_df['PLATE APPROVAL STATUS'].str.upper() == 'PASS')
        & (qaqc_df['APPROVAL STATUS'].str.upper() == 'PASS')
    )
    qaqc_pass_df = qaqc_df[pass_mask].copy()

    # ————— 2) Catch inconsistent sample PASS on a failed plate —————
    inconsistent = (
        (qaqc_df['PLATE APPROVAL STATUS'].str.upper() == 'FAIL') &
        (qaqc_df['APPROVAL STATUS'].str.upper() == 'PASS')
    )
    if inconsistent.any():
        bad_rows = (inconsistent[inconsistent].index + qaqc_header + 1).tolist()
        issues.append(
            f"Inconsistent statuses at QA/QC row(s) {bad_rows}: "
            "PLATE APPROVAL='FAIL' but APPROVAL STATUS='PASS'."
        )
        return jsonify({'status': 'fail', 'summary': [], 'issues': issues})

    # ————— 3) Now filter to bona‐fide PASS samples —————
    pass_mask = (
        (qaqc_df['PLATE APPROVAL STATUS'].str.upper() == 'PASS') &
        (qaqc_df['APPROVAL STATUS'].str.upper() == 'PASS')
    )
    qaqc_pass_df = qaqc_df[pass_mask].copy()


    # Step 1: check duplicates
    if 'SAMPLE ALIAS' not in qaqc_pass_df.columns:
        issues.append("Missing 'SAMPLE ALIAS' column in QA/QC Report.")
        return jsonify({'status': 'fail', 'summary': summary, 'issues': issues})

    qaqc_pass_df['SAMPLE ALIAS'] = qaqc_pass_df['SAMPLE ALIAS'].astype(str).str.strip()
    alias_duplicates = qaqc_pass_df.duplicated(subset='SAMPLE ALIAS', keep=False)
    duplicated_df = qaqc_pass_df[alias_duplicates]
    if not duplicated_df.empty:
        dup_counts = duplicated_df['SAMPLE ALIAS'].value_counts()
        for alias, count in dup_counts.items():
            issues.append(f"Duplicate PASS entries found for sample alias '{alias}' ({count} rows)")
        qaqc_pass_df = qaqc_pass_df.drop_duplicates(subset='SAMPLE ALIAS', keep='first')
    else:
        summary.append("Each sample has a single PASS entry in QA/QC (no duplicates found).")

    # Step 2: row‐count alignment
    if len(qaqc_pass_df) != len(customer_df):
        issues.append(
            f"Row count mismatch after filtering QA/QC PASS entries: "
            f"Customer={len(customer_df)}, QA/QC={len(qaqc_pass_df)}"
        )
        status = 'fail'
    else:
        summary.append("Filtered QA/QC rows match Customer rows in count and order.")

    # Step 3: compare selected fields
    compare_fields = ['SUBJECT ID', 'CALCULATED CONCENTRATION', 'CV%']
    # always show which columns we will compare
    present_fields = [
        f for f in compare_fields
        if f in customer_df.columns and f in qaqc_pass_df.columns
    ]
    if present_fields:
        summary.append(f"Compared columns: {', '.join(present_fields)}")

    mismatches = []
    for field in present_fields:
        for i, (val_c, val_q) in enumerate(zip(customer_df[field], qaqc_pass_df[field]), start=1):
            norm_c = str(val_c).strip().upper()
            norm_q = str(val_q).strip().upper()
            if norm_c == 'N/A': norm_c = ''
            if norm_q == 'N/A': norm_q = ''
            if norm_c != norm_q:
                mismatches.append(
                    f"Row {i}, column '{field}': Customer='{val_c or '[blank]'}', "
                    f"QA/QC='{val_q or '[blank]'}'"
                )

    if mismatches:
        issues.extend(mismatches)
        status = 'fail'
    else:
        summary.append("All values match between files.")

    return jsonify({'status': status, 'summary': summary, 'issues': issues})
