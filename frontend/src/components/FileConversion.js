import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { FiPlus, FiMinus, FiDownload } from 'react-icons/fi';

const styles = {
  header: {
    backgroundColor: '#003366',
    color: '#fff',
    padding: '1.5rem 2rem',
    textAlign: 'center',
    fontFamily: 'Helvetica, Arial, sans-serif',
  },
  headerTitle: {
    margin: 0,
    fontSize: '2rem',
  },
  headerSubtitle: {
    margin: '0.5rem 0 0',
    fontSize: '1rem',
  },
  container: {
    fontFamily: 'Helvetica, Arial, sans-serif',
    color: '#003366',
    backgroundColor: '#cce5ff',
    minHeight: '100vh',
    padding: '2rem',
  },
  dropzone: {
    border: '2px dashed #003366',
    borderRadius: '8px',
    padding: '1rem',
    textAlign: 'center',
    cursor: 'pointer',
    maxWidth: '350px',
    margin: '0 auto 1.5rem',
    backgroundColor: '#fff',
    transition: 'background-color 0.2s, color 0.2s',
  },
  dropzoneLoaded: {
    backgroundColor: '#003366',
    color: '#fff',
  },
  sectionTitle: {
    fontSize: '1.2rem',
    color: '#003366',
    margin: '1.5rem 0 0.5rem',
  },
  metadataRow: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '1.5rem',
  },
  input: {
    flex: 1,
    padding: '0.5rem',
    fontSize: '1rem',
    borderRadius: '4px',
    border: '1px solid #ccc',
  },
  requiredContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    marginBottom: '1.5rem',
  },
  select: {
    width: '32%',
    padding: '0.75rem',
    fontSize: '1rem',
    borderRadius: '4px',
    border: '1px solid #ccc',
  },
  optionalHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.5rem',
  },
  iconButton: {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    backgroundColor: '#003366',
    border: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    color: '#fff',
    fontSize: '1rem',
    lineHeight: 1,
  },
  optionalRow: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '0.75rem',
    alignItems: 'center',
  },
  customInput: {
    flex: 1,
    padding: '0.5rem',
    fontSize: '1rem',
    borderRadius: '4px',
    border: '1px solid #ccc',
  },
  button: {
    backgroundColor: '#fa5a27',
    color: '#ffffff',
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginTop: '1rem',
  },
  formatSelector: {
    marginTop: '1rem',
    width: '150px',
    padding: '0.5rem',
    fontSize: '0.9rem',
    borderRadius: '4px',
    border: '1px solid #ccc',
  },
  downloadButton: {
    backgroundColor: '#003366',
    color: '#fff',
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginTop: '1rem',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
};

export default function FileConversion() {
  const [file, setFile] = useState(null);
  const [headers, setHeaders] = useState([]);
  const [productId, setProductId] = useState('');
  const [productVersion, setProductVersion] = useState('');
  const [subjectId, setSubjectId] = useState('');
  const [mercodiaId, setMercodiaId] = useState('');
  const [optional, setOptional] = useState([]);
  const [customHeaders, setCustomHeaders] = useState({});
  const [project, setProject] = useState('');
  const [subproject, setSubproject] = useState('');
  const [requestId, setRequestId] = useState('');
  const [outputFormat, setOutputFormat] = useState('excel');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [downloadFilename, setDownloadFilename] = useState('');

  const onDrop = accepted => setFile(accepted[0]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  useEffect(() => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    fetch('http://localhost:5050/transform/analyze-columns', {
      method: 'POST',
      body: formData,
    })
      .then(async res => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Could not read file');
        setHeaders(data.columns || []);
      })
      .catch(err => alert(`Error: ${err.message}`));
  }, [file]);

  const addOptional = () => setOptional(prev => [...prev, '']);
  const removeOptional = () => {
    setOptional(prev => prev.slice(0, -1));
    setCustomHeaders(prev => {
      const copy = { ...prev };
      delete copy[optional.length - 1];
      return copy;
    });
  };

  const handleOptionalChange = (i, val) => {
    setOptional(prev => prev.map((o, idx) => (idx === i ? val : o)));
    if (val !== 'CUSTOM') {
      setCustomHeaders(prev => {
        const copy = { ...prev };
        delete copy[i];
        return copy;
      });
    }
  };

  const submit = () => {
    if (!file) return alert('Please upload a file first');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('PRODUCT ID', productId);
    formData.append('PRODUCT VERSION', productVersion);
    formData.append('SUBJECT ID', subjectId);
    formData.append('MERCODIA ID', mercodiaId);
    formData.append('Project ID', project);
    formData.append('Subproject ID', subproject);
    formData.append('Request ID', requestId);
    formData.append('format', outputFormat);
    optional.forEach((opt, idx) => {
      formData.append('OPTIONAL', opt === 'CUSTOM' ? 'CUSTOM' : opt);
      if (opt === 'CUSTOM') {
        formData.append('CUSTOM', customHeaders[idx] || '');
      }
    });

    fetch('http://localhost:5050/transform/generate-manifest', {
      method: 'POST',
      body: formData,
    })
      .then(res => {
        const disposition = res.headers.get('Content-Disposition');
        let filename = 'sample_manifest';
        if (disposition && disposition.includes('filename=')) {
          filename = disposition
            .split('filename=')[1]
            .split(';')[0]
            .trim()
            .replace(/['"]/g, '');
        }
        return res.blob().then(blob => ({ blob, filename }));
      })
      .then(({ blob, filename }) => {
        setDownloadFilename(filename);
        setDownloadUrl(URL.createObjectURL(blob));
      })
      .catch(err => alert(err.message));
  };

  const dzStyle = file ? { ...styles.dropzone, ...styles.dropzoneLoaded } : styles.dropzone;

  return (
    <>
      <header style={styles.header}>
        <h1 style={styles.headerTitle}>LIMS Converter</h1>
      </header>

      <div style={styles.container}>
        <div {...getRootProps()} style={dzStyle}>
          <input {...getInputProps()} />
          {file
            ? file.name
            : isDragActive
            ? 'Drop file here…'
            : 'Drag & drop your sample list, or click to select'}
        </div>

        <h4 style={styles.sectionTitle}>Project Metadata</h4>
        <div style={styles.metadataRow}>
          <input
            style={styles.input}
            placeholder="Project ID"
            value={project}
            onChange={e => setProject(e.target.value)}
          />
          <input
            style={styles.input}
            placeholder="Subproject ID"
            value={subproject}
            onChange={e => setSubproject(e.target.value)}
          />
          <input
            style={styles.input}
            placeholder="Request ID"
            value={requestId}
            onChange={e => setRequestId(e.target.value)}
          />
        </div>

        <h4 style={styles.sectionTitle}>Required Columns</h4>
        <div style={styles.requiredContainer}>
          {[
            ['PRODUCT ID', productId, setProductId],
            ['PRODUCT VERSION', productVersion, setProductVersion],
            ['SUBJECT ID', subjectId, setSubjectId],
            ['MERCODIA ID', mercodiaId, setMercodiaId],
          ].map(([label, val, setter], idx) => (
            <select
              key={idx}
              style={styles.select}
              value={val}
              onChange={e => setter(e.target.value)}
            >
              <option value="">{label}</option>
              {headers.map(h => (
                <option key={h} value={h}>
                  {val === h ? `${label} (${h})` : h}
                </option>
              ))}
            </select>
          ))}
        </div>

        <div style={styles.optionalHeader}>
          <h4 style={styles.sectionTitle}>Optional Columns</h4>
          <FiPlus style={styles.iconButton} onClick={addOptional} />
          {optional.length > 0 && <FiMinus style={styles.iconButton} onClick={removeOptional} />}
        </div>
        {optional.map((opt, i) => (
          <div key={i} style={styles.optionalRow}>
            <select
              value={opt}
              onChange={e => handleOptionalChange(i, e.target.value)}
              style={styles.select}
            >
              <option value="">(blank)</option>
              <option value="CUSTOM">Custom Header</option>
              {headers.map(h => (
                <option key={h} value={h}>
                  {h}
                </option>
              ))}
            </select>
            {opt === 'CUSTOM' && (
              <input
                style={styles.customInput}
                placeholder="Custom label"
                value={customHeaders[i] || ''}
                onChange={e => setCustomHeaders(prev => ({ ...prev, [i]: e.target.value }))}
              />
            )}
          </div>
        ))}

        <div style={{ marginTop: '1rem' }}>
          <label style={{ marginRight: '0.5rem' }}>Output format:</label>
          <select
            value={outputFormat}
            onChange={e => setOutputFormat(e.target.value)}
            style={styles.formatSelector}
          >
            <option value="excel">Excel (.xlsx)</option>
            <option value="csv">CSV (.csv)</option>
          </select>
        </div>

        <button style={styles.button} onClick={submit}>
          Generate Manifest
        </button>

        {downloadUrl && (
          <div>
            <button
              style={styles.downloadButton}
              onClick={() => {
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = downloadFilename;
                link.click();
              }}
            >
              <FiDownload />
              Download File
            </button>
          </div>
        )}
      </div>
    </>
  );
}
