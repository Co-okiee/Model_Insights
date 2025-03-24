import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import FileUpload from './FileUpload';
import ModelDetails from './ModelDetails';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4">
          <h1 className="text-3xl font-bold text-center mb-8">
            Machine Learning Model Insights
          </h1>
          <Routes>
            <Route path="/" element={<FileUpload />} />
            <Route path="/model-details" element={<ModelDetails />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
