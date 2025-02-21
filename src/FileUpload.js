import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, CheckCircle, AlertCircle } from 'lucide-react';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState(null); // 'success' | 'error' | null
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    handleFileSelection(droppedFile);
  };

  const handleFileSelection = (selectedFile) => {
    // Check if it's an h5 file
    if (selectedFile && selectedFile.name.endsWith('.h5')) {
      setFile(selectedFile);
      setStatus(null);
      setErrorMessage('');
    } else {
      setFile(null);
      setStatus('error');
      setErrorMessage('Please select a valid .h5 model file');
    }
  };

  const handleFileInput = (e) => {
    handleFileSelection(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsLoading(true);
    setProgress(0);
    setStatus(null);

    // Create form data to send to the backend
    const formData = new FormData();
    formData.append('model', file);

    try {
      // Send file to the backend via axios
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        // Monitor upload progress
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percent);
        },
      });

      // Handle success response
      if (response.status === 200) {
        setStatus('success');
      }
    } catch (error) {
      setStatus('error');
      setErrorMessage('Upload failed. Please try again.');
      console.error('Upload error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="file-upload">
      <div 
        className={`upload-zone ${isDragging ? 'dragging' : ''} ${isLoading ? 'loading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="file-icon">
          <Upload size={24} />
        </div>
        
        <p>Drag & drop your model file here or click to browse</p>
        {file && <p className="text-secondary">Selected: {file.name}</p>}
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".h5"
          onChange={handleFileInput}
          style={{ display: 'none' }}
        />
      </div>

      {file && (
        <div className="progress-bar">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {status === 'success' && (
        <div className="success">
          <CheckCircle size={20} />
          Model uploaded successfully!
        </div>
      )}

      {status === 'error' && (
        <div className="error">
          <AlertCircle size={20} />
          {errorMessage}
        </div>
      )}

      {file && !isLoading && status !== 'success' && (
        <button 
          className="upload-button"
          onClick={handleUpload}
          disabled={isLoading}
        >
          {isLoading ? 'Uploading...' : 'Upload Model'}
        </button>
      )}
    </div>
  );
};

export default FileUpload;
