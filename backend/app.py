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

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'h5'}

CORS(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_model_summary(h5_file_path):
    """
    Comprehensive model summary extraction with improved error handling
    """
    try:
        with h5py.File(h5_file_path, 'r') as model_file:
            # Initialize detailed summary dictionary
            model_summary = {
                'model_name': os.path.basename(h5_file_path),
                'total_layers': 0,
                'total_parameters': 0,
                'optimizer': model_file.attrs.get('optimizer', 'Not specified').decode('utf-8') if 'optimizer' in model_file.attrs else 'Not specified',
                'loss_function': model_file.attrs.get('loss', 'Not specified').decode('utf-8') if 'loss' in model_file.attrs else 'Not specified',
                'layers': []
            }

            # Recursive function to explore model structure
            def explore_groups(name, obj):
                if isinstance(obj, h5py.Group):
                    # Check for weights in the group
                    layer_params = 0
                    layer_details = {
                        'name': name,
                        'type': 'Unknown',
                        'parameters': 0,
                        'weights': []
                    }

                    # Explore weights in the group
                    if hasattr(obj, 'keys'):
                        for weight_name in obj.keys():
                            try:
                                weight = obj[weight_name]
                                if isinstance(weight, h5py.Dataset):
                                    weight_shape = weight.shape
                                    weight_params = np.prod(weight_shape)
                                    layer_params += weight_params

                                    # Try to infer layer type
                                    if 'kernel' in weight_name.lower():
                                        layer_details['type'] = 'Convolutional' if len(weight_shape) > 2 else 'Dense'
                                    
                                    layer_details['weights'].append({
                                        'name': weight_name,
                                        'shape': list(weight_shape),
                                        'parameters': int(weight_params)
                                    })
                            except Exception as weight_err:
                                print(f"Error processing weight {weight_name}: {weight_err}")

                    # Update layer details
                    layer_details['parameters'] = int(layer_params)
                    
                    # Only add layers with parameters
                    if layer_params > 0:
                        model_summary['layers'].append(layer_details)
                        model_summary['total_parameters'] += layer_params
                        model_summary['total_layers'] += 1

            # Traverse the H5 file structure
            model_file.visititems(explore_groups)

            return model_summary

    except Exception as e:
        print(f"Comprehensive error in model summary extraction: {e}")
        return {
            'error': str(e),
            'model_name': os.path.basename(h5_file_path),
            'details': 'Failed to extract model summary'
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

            # Save extracted info to a JSON file
            json_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}_contents.json")
            with open(json_path, 'w') as json_file:
                json.dump(model_summary, json_file, indent=2)

            return jsonify({
                "message": "File processed successfully",
                "model_info": model_summary,
                "json_path": json_path
            }), 200

        except Exception as e:
            return jsonify({
                "error": f"Failed to process H5 file: {str(e)}"
            }), 500

    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)