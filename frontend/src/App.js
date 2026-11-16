import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import FileAnalysis from './components/FileAnalysis';
import FileConversion from './components/FileConversion';
import NavMenu from './components/NavMenu';

function App() {
  return (
    <Router>
      <div style={{ fontFamily: 'Helvetica, sans-serif' }}>
        {/* Navigation menu icon shown on all pages */}
        <NavMenu />
        <div style={{ padding: 20 }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/file-analysis" element={<FileAnalysis />} />
            <Route path="/file-conversion" element={<FileConversion />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
