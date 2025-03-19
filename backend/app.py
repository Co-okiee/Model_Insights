import os
import h5py
import numpy as np
import json
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'h5'}

CORS(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_model_info(h5file):
    """
    Extract only key details from an H5 model file.
    """
    model_info = {
        "layers": [],
        "total_parameters": 0,
        "optimizer": None,
        "loss_function": None
    }

    try:
        # Extracting model architecture if stored
        if "model_config" in h5file.attrs:
            model_info["architecture"] = json.loads(h5file.attrs["model_config"])

        # Extract optimizer and loss function if stored
        model_info["optimizer"] = h5file.attrs.get("optimizer", "").decode("utf-8") if "optimizer" in h5file.attrs else None
        model_info["loss_function"] = h5file.attrs.get("loss", "").decode("utf-8") if "loss" in h5file.attrs else None

        def visit_layer(name, obj):
            if isinstance(obj, h5py.Group):
                # Extract layer details
                layer = {"name": name, "weights": 0, "trainable": None}

                # Check if the group contains weight names (indicating a layer)
                if "weight_names" in obj.attrs:
                    layer["weights"] = len(obj.attrs["weight_names"])

                # Check if the layer has a trainable attribute
                layer["trainable"] = obj.attrs.get("trainable", "Unknown")

                # Add to model info
                model_info["layers"].append(layer)

        h5file.visititems(visit_layer)

        # Total parameters count
        model_info["total_parameters"] = sum(layer["weights"] for layer in model_info["layers"])

    except Exception as e:
        return {"error": f"Failed to extract model info: {str(e)}"}

    return model_info

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
                model_info = extract_model_info(f)

                # Save extracted info to a JSON file
                json_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}_contents.json")
                with open(json_path, 'w') as json_file:
                    json.dump(model_info, json_file, indent=2)

            return jsonify({
                "message": "File processed successfully",
                "model_info": model_info,
                "json_path": json_path
            }), 200

        except Exception as e:
            return jsonify({
                "error": f"Failed to process H5 file: {str(e)}"
            }), 500

    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True)
