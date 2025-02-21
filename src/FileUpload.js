import React, { useState } from 'react';
import axios from 'axios';
import { Button, TextField } from '@mui/material';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file.");
      return;
    }
  
    setError('');  // Reset previous errors
  
    const formData = new FormData();
    formData.append('model', file);  // Ensure 'model' matches the backend field name
  
    console.log("Uploading file:", file);  // Log file to ensure it's correct
    
    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
  
      console.log('File upload response:', response.data);  // Log success response
    } catch (err) {
      console.error('Error uploading the file:', err);
      setError('Error uploading file. Please try again.');
    }
  };
  

  return (
    <div>
      <TextField
        variant="outlined"
        type="file"
        onChange={handleFileChange}
      />
      {error && <div style={{ color: 'red' }}>{error}</div>}
      <Button variant="contained" color="primary" onClick={handleUpload}>
        Upload Model
      </Button>
    </div>
  );
};

export default FileUpload;
