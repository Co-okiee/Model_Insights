import os
import json
import re
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'json', 'py'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_model_details(content):
    """
    Custom parsing logic to extract model details from file content
    This is a basic implementation and should be enhanced based on your specific file formats
    """
    model_data = {
        'total_layers': 0,
        'total_parameters': 0,
        'optimizer': 'N/A',
        'loss_function': 'N/A',
        'layers': []
    }

    # Extract total layers (example regex)
    layers_match = re.findall(r'layer(\d+)', content, re.IGNORECASE)
    model_data['total_layers'] = len(layers_match)

    # Extract total parameters (example regex)
    params_match = re.findall(r'(\d+)\s*parameters', content, re.IGNORECASE)
    if params_match:
        model_data['total_parameters'] = sum(int(p) for p in params_match)

    # Try to find optimizer and loss function
    if 'adam' in content.lower():
        model_data['optimizer'] = 'Adam'
    if 'sgd' in content.lower():
        model_data['optimizer'] = 'SGD'
    
    if 'cross_entropy' in content.lower():
        model_data['loss_function'] = 'Cross Entropy'
    if 'mse' in content.lower():
        model_data['loss_function'] = 'Mean Squared Error'

    # Extract layer information
    layer_matches = re.findall(r'(Dense|Conv2D|LSTM)\s*\(\s*(\d+)\s*\)', content)
    model_data['layers'] = [
        {
            'name': f'{layer_type} Layer',
            'type': layer_type,
            'parameters': int(params)
        } for layer_type, params in layer_matches
    ]

    return model_data

def parse_model_file(file_path):
    try:
        # Detect file type and parse accordingly
        file_ext = os.path.splitext(file_path)[1].lower()
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        if file_ext == '.json':
            # If it's a JSON file, load directly
            model_data = json.load(f)
        else:
            # Use custom parsing for text/Python files
            model_data = extract_model_details(content)
        
        return {
            'total_layers': model_data.get('total_layers', 0),
            'total_parameters': model_data.get('total_parameters', 0),
            'optimizer': model_data.get('optimizer', 'N/A'),
            'loss_function': model_data.get('loss_function', 'N/A'),
            'layers': model_data.get('layers', [])
        }
    except Exception as e:
        return {
            'error': str(e)
        }

@app.route('/upload-model-file', methods=['POST'])
def upload_model_file():
    # Check if file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check if file is allowed
    if file and allowed_file(file.filename):
        # Secure the filename and save it
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the file
        file.save(filepath)
        
        # Parse the model file
        model_summary = parse_model_file(filepath)
        
        # Optional: Remove the file after processing
        os.remove(filepath)
        
        return jsonify(model_summary)
    
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True)