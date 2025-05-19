// This is the unified and updated FileAnalysis.js file
// It preserves all of your existing logic, UI, styles, and message handling
// Adds toggle buttons styled according to selected/unselected state

import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const styles = {
  container: {
    fontFamily: 'Helvetica, Arial, sans-serif',
    color: '#003366',
    backgroundColor: '#cce5ff',
    minHeight: '100vh',
    padding: '2rem',
  },
  header: {
    backgroundColor: '#003366',
    color: '#fff',
    padding: '1.5rem 2rem',
    textAlign: 'center',
  },
  headerTitle: {
    margin: 0,
    fontSize: '2rem',
  },
  toggleContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginTop: '1rem',
    gap: '1rem',
  },
  toggleButton: (active) => ({
    backgroundColor: active ? '#003366' : '#cce5ff',
    color: active ? '#fff' : '#003366',
    border: `2px solid #003366`,
    padding: '0.75rem 1.5rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
  }),
  fileArea: {
    display: 'flex',
    justifyContent: 'center',
    gap: '6rem',
    marginTop: '2rem',
    marginBottom: '1rem',
  },
  dropzoneContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '300px',
  },
  label: {
    marginBottom: '0.5rem',
    fontWeight: 'bold',
    fontSize: '1.1rem',
  },
  dropzone: {
    border: '2px dashed #003366',
    borderRadius: '8px',
    padding: '2rem',
    textAlign: 'center',
    cursor: 'pointer',
    width: '100%',
    height: '120px',
    backgroundColor: '#fff',
    transition: 'background-color 0.2s, color 0.2s',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  dropzoneLoaded: {
    backgroundColor: '#003366',
    color: '#fff',
  },
  buttonContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginTop: '1.5rem',
  },
  button: {
    backgroundColor: '#fa5a27',
    color: '#ffffff',
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginRight: '1rem',
  },
  resultBox: {
    marginTop: '2rem',
    padding: '1rem',
    backgroundColor: '#ffffff',
    border: '2px solid #003366',
    borderRadius: '12px',
    whiteSpace: 'pre-wrap',
    maxWidth: '800px',
    marginLeft: 'auto',
    marginRight: 'auto',
    overflowX: 'auto',
  },
  greenBox: {
    borderLeft: '4px solid green',
    backgroundColor: '#f0fff4',
    padding: '0.5rem',
    marginBottom: '0.5rem',
    borderRadius: '4px',
  },
  redBox: {
    borderLeft: '4px solid red',
    backgroundColor: '#fff0f0',
    padding: '0.5rem',
    marginBottom: '0.5rem',
    borderRadius: '4px',
  },
};

export default function FileAnalysis() {
  const [mode, setMode] = useState('manifest');
  const [manifestFile, setManifestFile] = useState(null);
  const [reportFile, setReportFile] = useState(null);
  const [qaFile, setQAFile] = useState(null);
  const [result, setResult] = useState(null);

  const manifestDrop = useDropzone({ onDrop: accepted => setManifestFile(accepted[0]) });
  const reportDrop = useDropzone({ onDrop: accepted => setReportFile(accepted[0]) });
  const qaDrop = useDropzone({ onDrop: accepted => setQAFile(accepted[0]) });

  const handleSubmit = () => {
    const formData = new FormData();
    if (mode === 'manifest') {
      if (!manifestFile || !reportFile) {
        setResult({ error: 'Please upload both files' });
        return;
      }
      formData.append('manifest', manifestFile);
      formData.append('report', reportFile);
      fetch('http://localhost:5050/file-analysis/review', {
        method: 'POST',
        body: formData,
      })
        .then(res => res.json())
        .then(data => {
          const uniqueIssues = Array.from(new Set(data.issues));
          setResult({ data: { ...data, issues: uniqueIssues } });
        })
        .catch(err => setResult({ error: err.message }));
    } else {
      if (!reportFile || !qaFile) {
        setResult({ error: 'Please upload both QA/QC files' });
        return;
      }
      formData.append('customer', reportFile);
      formData.append('qaqc', qaFile);
      fetch('http://localhost:5050/file-analysis/review-qaqc', {
        method: 'POST',
        body: formData,
      })
        .then(res => res.json())
        .then(data => setResult({ data }))
        .catch(err => setResult({ error: err.message }));
    }
  };

  const dzStyle = (file) => (file ? { ...styles.dropzone, ...styles.dropzoneLoaded } : styles.dropzone);

  return (
    <>
      <header style={styles.header}>
      <h1 style={styles.headerTitle}>Quality Check</h1>
      </header>

      <div style={styles.container}>
        <div style={styles.toggleContainer}>
          <button
            style={styles.toggleButton(mode === 'manifest')}
            onClick={() => setMode('manifest')}
          >
            Sample Manifest and Report
          </button>
          <button
            style={styles.toggleButton(mode === 'qaqc')}
            onClick={() => setMode('qaqc')}
          >
            Customer Report and QA/QC
          </button>
        </div>

        <div style={styles.fileArea}>
          {mode === 'manifest' ? (
            <>
              <div style={styles.dropzoneContainer}>
                <div style={styles.label}>Sample Manifest</div>
                <div {...manifestDrop.getRootProps()} style={dzStyle(manifestFile)}>
                  <input {...manifestDrop.getInputProps()} />
                  {manifestFile ? manifestFile.name : manifestDrop.isDragActive ? 'Drop here…' : 'Drag & drop or click to select'}
                </div>
              </div>
              <div style={styles.dropzoneContainer}>
                <div style={styles.label}>Customer Report</div>
                <div {...reportDrop.getRootProps()} style={dzStyle(reportFile)}>
                  <input {...reportDrop.getInputProps()} />
                  {reportFile ? reportFile.name : reportDrop.isDragActive ? 'Drop here…' : 'Drag & drop or click to select'}
                </div>
              </div>
            </>
          ) : (
            <>
              <div style={styles.dropzoneContainer}>
                <div style={styles.label}>Customer Report</div>
                <div {...reportDrop.getRootProps()} style={dzStyle(reportFile)}>
                  <input {...reportDrop.getInputProps()} />
                  {reportFile ? reportFile.name : reportDrop.isDragActive ? 'Drop here…' : 'Drag & drop or click to select'}
                </div>
              </div>
              <div style={styles.dropzoneContainer}>
                <div style={styles.label}>QA/QC Report</div>
                <div {...qaDrop.getRootProps()} style={dzStyle(qaFile)}>
                  <input {...qaDrop.getInputProps()} />
                  {qaFile ? qaFile.name : qaDrop.isDragActive ? 'Drop here…' : 'Drag & drop or click to select'}
                </div>
              </div>
            </>
          )}
        </div>

        <div style={styles.buttonContainer}>
          <button style={styles.button} onClick={handleSubmit}>Analyze Files</button>
        </div>

        {result && (
          <div style={styles.resultBox}>
            {result.error ? (
              <div style={{ color: 'red' }}>Error: {result.error}</div>
            ) : (
              <div>

                {result.data.status === 'pass' && (
                  <div style={{ color: 'green' }}>
                    ✅ Everything is correct! No issues found.
                    {result.data.summary.map((msg, idx) => (
                      <div key={idx} style={styles.greenBox}>{msg}</div>
                    ))}
                  </div>
                )}


                {result.data.status !== 'pass' && (
                  <div>
                    {result.data.summary && result.data.summary.length > 0 && (
                      <div>
                        <h3 style={{ color: 'green' }}>✅ Correct Parts</h3>
                        {result.data.summary.map((item, idx) => (
                          <div key={idx} style={styles.greenBox}>{item}</div>
                        ))}
                      </div>
                    )}


                    {result.data.issues && result.data.issues.length > 0 && (
                      <div>
                        <h3 style={{ color: 'red', marginTop: '1rem' }}>⚠️ Issues Found</h3>
                        {result.data.issues.map((item, idx) => (
                          <div key={idx} style={styles.redBox}>{item}</div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}