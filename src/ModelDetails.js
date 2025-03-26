import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ModelDetails.css';

const ModelDetails = () => {
  const [modelSummary, setModelSummary] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Fetch model summary from backend
  const fetchModelSummary = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/model-summary', {
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      setModelSummary(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Detailed error:', err);
      setError(err.response?.data?.error || err.message || 'Failed to load model summary');
      setLoading(false);
    }
  };

  // Analyze model using Groq
  const handleAnalyzeModel = async () => {
    if (!modelSummary) {
      setError('No model summary available');
      return;
    }

    const GROQ_API_KEY = process.env.REACT_APP_GROQ_API_KEY;
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        'https://api.groq.com/openai/v1/chat/completions',
        {
          model: 'llama-3.3-70b-versatile',
          messages: [
            {
              role: 'system',
              content: 'You are a detailed AI assistant analyzing machine learning model architectures.'
            },
            {
              role: 'user',
              content: `Provide a comprehensive analysis of this machine learning model summary:
                Model Name: ${modelSummary.model_name || 'Unnamed Model'}
                Total Layers: ${modelSummary.total_layers}
                Total Parameters: ${modelSummary.total_parameters}
                Optimizer: ${modelSummary.optimizer}
                Loss Function: ${modelSummary.loss_function}
                
                Detailed Layer Information:
                ${JSON.stringify(modelSummary.layers, null, 2)}
                
                Provide insights into the model's architecture, potential strengths, and areas for optimization.`
            }
          ],
          temperature: 0.7,
          max_tokens: 500
        },
        {
          headers: {
            'Authorization': `Bearer ${GROQ_API_KEY}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const groqAnalysis = response.data?.choices?.[0]?.message?.content || 'No analysis available';
      setAnalysis(groqAnalysis);

    } catch (err) {
      console.error('Analysis error:', err);
      
      let errorMessage = 'An unexpected error occurred';
      if (err.response) {
        errorMessage = err.response.data?.error?.message || 
                       `Groq API Error: ${err.response.status}`;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Toggle dark mode
  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.body.classList.toggle('dark-mode');
  };

  // Fetch model summary on component mount
  useEffect(() => {
    fetchModelSummary();
  }, []);

  // Render loading and error states
  if (loading) return <div className="loading">Loading model summary...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  // Render component
  return (
    <div className={`model-details-container ${isDarkMode ? 'dark-mode' : 'light-mode'}`}>
      <div className="mode-toggle">
        <button onClick={toggleDarkMode}>
          {isDarkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
        </button>
      </div>


      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {modelSummary && (
        <>
          <div className="model-summary card">
            <h3>Model Summary</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="label">Model Name</span>
                <span className="value">{modelSummary.model_name || 'N/A'}</span>
              </div>
              <div className="summary-item">
                <span className="label">Total Layers</span>
                <span className="value">{modelSummary.total_layers || 0}</span>
              </div>
              <div className="summary-item">
                <span className="label">Total Parameters</span>
                <span className="value">{modelSummary.total_parameters || 0}</span>
              </div>
              <div className="summary-item">
                <span className="label">Optimizer</span>
                <span className="value">{modelSummary.optimizer || 'N/A'}</span>
              </div>
              <div className="summary-item">
                <span className="label">Loss Function</span>
                <span className="value">{modelSummary.loss_function || 'N/A'}</span>
              </div>
            </div>
          </div>

          <button 
            onClick={handleAnalyzeModel}
            disabled={loading}
            className="analyze-button"
          >
            {loading ? 'Analyzing...' : 'Analyze Model with Groq'}
          </button>

          {analysis && (
  <div className="analysis-result card">
    <h3>Groq Model Analysis</h3>
    <div className="analysis-section">
      <div className="section-header">🏗️ Model Architecture Overview</div>
      <div className="section-content">
        <p className="bullet-point">
          A deep neural network architecture, specifically a <span className="highlight">Convolutional Neural Network (CNN)</span>
        </p>
      </div>
    </div>

    <div className="analysis-section">
      <div className="section-header">📊 Layer Breakdown</div>
      <div className="section-content">
        <div className="bullet-point">
          <span className="highlight">Convolutional Layers</span>: 6 layers with varying filter sizes
          <ul>
            <li><code>conv2d</code>: 3x3x32</li>
            <li><code>conv2d_1</code>: 3x3x32x64</li>
            <li><code>conv2d_5</code>: 3x3x32x64 (or 3x3x64x64)</li>
          </ul>
        </div>
        <div className="bullet-point">
          <span className="highlight">Dense Layers</span>: 2 layers with 16,448 and 130 parameters
          <ul>
            <li><code>dense</code>: 256x64</li>
            <li><code>dense_1</code>: 1x64x2</li>
          </ul>
        </div>
      </div>
    </div>

    <div className="analysis-section">
      <div className="section-header">💪 Potential Strengths</div>
      <div className="section-content">
        <div className="bullet-point">
          <span className="highlight">Deep Architecture</span>: Suitable for complex tasks
        </div>
        <div className="bullet-point">
          <span className="highlight">Multiple Convolutional Layers</span>: Enhanced feature extraction
        </div>
        <div className="bullet-point">
          <span className="highlight">Dense Layers</span>: High-level performance capabilities
        </div>
      </div>
    </div>

    <div className="analysis-section">
      <div className="section-header">🔧 Areas for Optimization</div>
      <div className="section-content">
        <div className="bullet-point">
          <span className="highlight">Optimizer Uncertainty</span>: Loss function and optimizer not specified
        </div>
        <div className="bullet-point">
          <span className="highlight">Model Complexity</span>: 551,048 parameters risk potential overfitting
        </div>
        <div className="bullet-point">
          <span className="highlight">Convolutional Layer Parameters</span>: High parameter count in conv layers
        </div>
      </div>
    </div>
  </div>
)}
          <div className="layer-details card">
            <h3>Layer Breakdown</h3>
            <table>
              <thead>
                <tr>
                  <th>Layer Name</th>
                  <th>Layer Type</th>
                  <th>Parameters</th>
                </tr>
              </thead>
              <tbody>
                {modelSummary.layers?.map((layer, index) => (
                  <tr key={index}>
                    <td>{layer.name || `Layer ${index + 1}`}</td>
                    <td>{layer.type || 'Unknown'}</td>
                    <td>{layer.parameters || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default ModelDetails;