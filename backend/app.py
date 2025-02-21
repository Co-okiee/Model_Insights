import os
import h5py
import numpy as np
import tempfile
import json
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'h5', 'onnx'}

CORS(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_h5_contents(h5file):
    """
    Recursively extract contents of an H5 file including datasets, attributes, and group structure.
    """
    contents = {}
    
    def convert_to_native(value):
        """Convert numpy types to native Python types for JSON serialization."""
        if isinstance(value, np.ndarray):
            # Convert numpy arrays to lists
            return value.tolist()
        elif isinstance(value, (np.int64, np.int32)):
            # Convert numpy integers to Python integers
            return int(value)
        elif isinstance(value, (np.float32, np.float64)):
            # Convert numpy floats to Python floats
            return float(value)
        elif isinstance(value, bytes):
            # Convert bytes to string
            return value.decode('utf-8')
        return value

    def extract_attributes(obj):
        """Extract attributes of a dataset or group."""
        attrs = {}
        for key, value in obj.attrs.items():
            attrs[key] = convert_to_native(value)
        return attrs

    def visit_item(name, obj):
        """Process each item (dataset or group) in the H5 file."""
        if isinstance(obj, h5py.Dataset):
            item_info = {
                'type': 'dataset',
                'shape': obj.shape,
                'dtype': str(obj.dtype),
                'attributes': extract_attributes(obj)
            }
            
            # For small datasets, include the actual data
            if np.prod(obj.shape) < 1000:  # Limit to avoid memory issues
                try:
                    data = obj[()]
                    item_info['data'] = convert_to_native(data)
                except Exception as e:
                    item_info['data_error'] = str(e)
            else:
                item_info['data'] = f"Large dataset: {np.prod(obj.shape)} elements"
                
        elif isinstance(obj, h5py.Group):
            item_info = {
                'type': 'group',
                'attributes': extract_attributes(obj)
            }
            
        contents[name] = item_info
        
    h5file.visititems(visit_item)
    
    # Add root level attributes
    contents['root_attributes'] = extract_attributes(h5file)
    
    return contents

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
            with h5py.File(file_path, 'r') as f:
                # Extract detailed contents
                contents = extract_h5_contents(f)
                
                # Store the extracted information in a JSON file
                json_path = os.path.join(UPLOAD_FOLDER, f"{filename}_contents.json")
                with open(json_path, 'w') as json_file:
                    json.dump(contents, json_file, indent=2)
                
                # Generate a basic summary
                summary = {
                    "filename": filename,
                    "total_items": len(contents) - 1,  # Subtract 1 for root_attributes
                    "groups": sum(1 for item in contents.values() if isinstance(item, dict) and item.get('type') == 'group'),
                    "datasets": sum(1 for item in contents.values() if isinstance(item, dict) and item.get('type') == 'dataset'),
                    "root_attributes": len(contents.get('root_attributes', {}))
                }
                
                return jsonify({
                    "message": "File processed successfully",
                    "summary": summary,
                    "contents": contents
                }), 200

        except Exception as e:
            return jsonify({
                "error": f"Failed to process H5 file: {str(e)}"
            }), 500

    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True)