import React from 'react';
import { Link } from 'react-router-dom';
import logofull from '../designs/logofull.png';

const HomePage = () => {
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    backgroundColor: '#cce5ff',
  };
  const buttonStyle = {
    backgroundColor: '#003366',
    color: 'white',
    padding: '15px 30px',
    border: 'none',
    borderRadius: '5px',
    fontSize: '18px',
    cursor: 'pointer',
    margin: '10px',
    fontFamily: 'Helvetica, sans-serif',
  };

  return (
    <div style={containerStyle}>
      {/* fulllogo */}
      <img
        src={logofull}
        alt="Mercodia Logo"
        style={{ width: '400px', marginBottom: '1.0rem' }}
      />

      <div>
        <Link to="/file-conversion">
          <button style={buttonStyle}>LIMS Converter</button>
        </Link>
        <Link to="/file-analysis">
          <button style={buttonStyle}>Quality Check</button>
        </Link>
      </div>
    </div>
  );
};

export default HomePage;
