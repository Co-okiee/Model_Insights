import os
import h5py
import numpy as np
import json
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

MAX_FILE_SIZE_MB = 100  # Maximum file size in MB
MAX_COMPLETION_TOKENS = 32768  # Maximum completion tokens


UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'h5'}

CORS(app)

def check_file_size(file_path):
    """
    Check if file size is within the allowed limit
    """
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File size exceeds maximum limit of {MAX_FILE_SIZE_MB} MB")


def truncate_payload(data, max_tokens=6000):
    """
    Aggressively truncate the payload to fit within token limits
    """
    while True:
        # Convert to JSON
        payload = json.dumps(data)
        
        # Check if payload exceeds limit
        if len(payload.encode('utf-8')) <= max_tokens:
            return data
        
        # Aggressive reduction strategies
        if isinstance(data, dict):
            # Remove least important keys first
            keys_to_remove = [
                'weights', 
                'layers', 
                'details', 
                'json_path'
            ]
            for key in keys_to_remove:
                if key in data:
                    del data[key]
        
        # If still too large, further reduce
        if isinstance(data, dict) and 'model_info' in data:
            data['model_info'] = {
                'model_name': data['model_info'].get('model_name', 'Unknown'),
                'total_layers': data['model_info'].get('total_layers', 0),
                'total_parameters': data['model_info'].get('total_parameters', 0)
            }
        
        # Last resort: return minimal information
        if len(json.dumps(data).encode('utf-8')) > max_tokens:
            return {
                'error': 'Payload exceeded size limits',
                'message': 'Unable to transmit full model details'
            }

import time
from functools import wraps

def rate_limit_handler(max_retries=3, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    # Truncate payload before sending
                    if 'data' in kwargs:
                        kwargs['data'] = truncate_payload(kwargs['data'])
                    
                    response = func(*args, **kwargs)
                    return response
                
                except Exception as e:
                    if "Request too large" in str(e):
                        retries += 1
                        wait_time = backoff_factor ** retries
                        print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise
            
            raise Exception("Max retries exceeded. Unable to process request.")
        return wrapper
    return decorator

def truncate_model_summary(model_summary, max_tokens=32768):
    """
    Intelligently truncate the model summary to fit within token limits
    """
    # Create a copy to avoid modifying the original
    truncated_summary = model_summary.copy()
    
    # First, trim excessive details from layer weights
    for layer in truncated_summary.get('layers', []):
        if 'weights' in layer:
            # Limit weights to essential information
            trimmed_weights = []
            for weight in layer['weights']:
                trimmed_weight = {
                    'name': weight['name'],
                    'shape': weight['shape'][:2],  # Keep only first two dimensions
                    'parameters': weight['parameters']
                }
                trimmed_weights.append(trimmed_weight)
            layer['weights'] = trimmed_weights[:3]  # Keep only first 3 weights
    
    # Limit total layers
    truncated_summary['layers'] = truncated_summary.get('layers', [])[:50]
    
    # Implement a recursive truncation to ensure token limit
    while True:
        # Convert to JSON to check token size
        summary_json = json.dumps(truncated_summary)
        
        # If within token limit, return
        if len(summary_json.encode('utf-8')) <= max_tokens:
            return truncated_summary
        
        # If still too large, further reduce details
        if truncated_summary['layers']:
            # Remove the last layer
            truncated_summary['layers'].pop()
        else:
            # If no layers left, return a minimal summary
            return {
                'model_name': truncated_summary.get('model_name', 'Unknown'),
                'total_layers': 0,
                'total_parameters': 0,
                'message': 'Summary truncated due to size limitations'
            }


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def intelligent_truncate_summary(model_summary, max_tokens=32768):
    """
    Intelligently truncate the model summary to fit within token limits
    
    Truncation Strategy:
    1. Preserve core metadata
    2. Progressively reduce layer details
    3. Ensure critical information remains
    """
    # Create a deep copy to avoid modifying original
    truncated = {
        'model_name': model_summary.get('model_name', 'Unknown Model'),
        'total_layers': model_summary.get('total_layers', 0),
        'total_parameters': model_summary.get('total_parameters', 0),
        'optimizer': model_summary.get('optimizer', 'Not specified'),
        'loss_function': model_summary.get('loss_function', 'Not specified'),
        'layers': []
    }
    
    # Get original layers
    original_layers = model_summary.get('layers', [])
    
    # Truncation phases
    truncation_phases = [
        # Phase 1: Keep most important layer details
        lambda layers: [
            {
                'name': layer.get('name', 'Unknown Layer'),
                'type': layer.get('type', 'Unknown'),
                'parameters': layer.get('parameters', 0)
            } for layer in layers[:100]  # Limit to first 100 layers
        ],
        
        # Phase 2: Further reduce layer details
        lambda layers: [
            {
                'name': layer.get('name', 'Unknown Layer'),
                'parameters': layer.get('parameters', 0)
            } for layer in layers[:50]  # Limit to first 50 layers
        ],
        
        # Phase 3: Minimal layer information
        lambda layers: [
            {
                'name': f"Layer {i+1}"
            } for i in range(min(len(layers), 10))  # Limit to 10 layer names
        ]
    ]
    
    # Try each truncation phase
    for phase in truncation_phases:
        # Apply current phase truncation
        truncated['layers'] = phase(original_layers)
        
        # Convert to JSON and check size
        summary_json = json.dumps(truncated)
        
        # If within token limit, return
        if len(summary_json.encode('utf-8')) <= max_tokens:
            return truncated
    
    # Absolute minimal summary if all else fails
    return {
        'model_name': truncated['model_name'],
        'total_layers': len(original_layers),
        'total_parameters': truncated['total_parameters'],
        'truncation_note': 'Extensive truncation applied due to size constraints'
    }

def extract_model_summary(h5_file_path):
    """
    Modified extraction to handle large summaries
    """
    try:
        with h5py.File(h5_file_path, 'r') as model_file:
            # Initial model summary extraction (existing logic)
            model_summary = {
                'model_name': os.path.basename(h5_file_path),
                'total_layers': 0,
                'total_parameters': 0,
                'optimizer': model_file.attrs.get('optimizer', 'Not specified').decode('utf-8') 
                    if 'optimizer' in model_file.attrs else 'Not specified',
                'loss_function': model_file.attrs.get('loss', 'Not specified').decode('utf-8') 
                    if 'loss' in model_file.attrs else 'Not specified',
                'layers': []
            }

            # Existing exploration logic for layers and parameters
            def explore_groups(name, obj):
                if isinstance(obj, h5py.Group):
                    layer_params = 0
                    layer_details = {
                        'name': name,
                        'type': 'Unknown',
                        'parameters': 0,
                        'weights': []
                    }

                    if hasattr(obj, 'keys'):
                        for weight_name in obj.keys():
                            try:
                                weight = obj[weight_name]
                                if isinstance(weight, h5py.Dataset):
                                    weight_shape = weight.shape
                                    weight_params = np.prod(weight_shape)
                                    layer_params += weight_params

                                    if 'kernel' in weight_name.lower():
                                        layer_details['type'] = 'Convolutional' if len(weight_shape) > 2 else 'Dense'
                                    
                                    layer_details['weights'].append({
                                        'name': weight_name,
                                        'shape': list(weight_shape),
                                        'parameters': int(weight_params)
                                    })
                            except Exception as weight_err:
                                print(f"Error processing weight {weight_name}: {weight_err}")

                    layer_details['parameters'] = int(layer_params)
                    
                    if layer_params > 0:
                        model_summary['layers'].append(layer_details)
                        model_summary['total_parameters'] += layer_params
                        model_summary['total_layers'] += 1

            # Traverse file structure
            model_file.visititems(explore_groups)

            # Intelligently truncate the summary
            return intelligent_truncate_summary(model_summary)

    except Exception as e:
        print(f"Error in model summary extraction: {e}")
        return {
            'error': str(e),
            'model_name': os.path.basename(h5_file_path),
            'details': 'Partial model summary extracted'
        }


@app.route('/api/model-summary', methods=['GET'])
def get_model_summary():
    # Find the most recent H5 file in the uploads folder
    h5_files = [
        os.path.join(UPLOAD_FOLDER, f) 
        for f in os.listdir(UPLOAD_FOLDER) 
        if f.endswith('.h5')
    ]

    if not h5_files:
        return jsonify({
            'error': 'No H5 files found',
            'details': 'Please upload a model file first'
        }), 404

    # Get the most recently modified H5 file
    latest_h5_file = max(h5_files, key=os.path.getmtime)
    
    model_summary = extract_model_summary(latest_h5_file)
    
    if not isinstance(model_summary, dict) or 'error' in model_summary:
        return jsonify(model_summary), 500
    
    return jsonify(model_summary)

@app.route('/upload', methods=['POST'])
@rate_limit_handler()
def upload_file():
    if 'model' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['model']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            model_summary = extract_model_summary(file_path)
            
        
            # Aggressive truncation before returning
            truncated_summary = truncate_payload(model_summary)
        

            # Save extracted info to a JSON file
            json_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}_contents.json")
            with open(json_path, 'w') as json_file:
                json.dump(model_summary, json_file, indent=2)

            return jsonify({
                "message": "File processed successfully",
                "model_info": model_summary,
                "json_path": json_path,
                "message": "File processed with size limitations",
                "model_info": truncated_summary
            }), 200

        except Exception as e:
            return jsonify({
                "error": f"Failed to process H5 file: {str(e)}"
            }), 500

    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)