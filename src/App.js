// App.js
import React from 'react';
import './App.css';
import FileUpload from './FileUpload';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-center mb-8">
          Machine Learning Model Insights
        </h1>
        <FileUpload />
      </div>
    </div>
  );
}

export default App;