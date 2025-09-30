import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SimpleDashboard from './pages/SimpleDashboard';
import EnhancedDashboard from './pages/EnhancedDashboard';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <div className="App">
        <Router>
          <Routes>
            <Route path="/" element={<Navigate to="/enhanced" replace />} />
            <Route path="/dashboard" element={<SimpleDashboard />} />
            <Route path="/enhanced" element={<EnhancedDashboard />} />
          </Routes>
        </Router>
      </div>
    </ErrorBoundary>
  );
}

export default App;