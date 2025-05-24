from flask import Blueprint, render_template, request, session, jsonify, g
import logging, json
import pandas as pd
from pathlib import Path
from machineLearning.trainModel import train_model
from machineLearning.makePredictions import makePreds
from dataBase.queryFeatures import getFeatures
from utils.path_helper import (
    get_data_source_config_path,
    get_model_config_dir,
    get_model_config_path,
    get_temp_upload_path
)

prediction_bp = Blueprint('prediction_bp', __name__)

@prediction_bp.route("/predictions", methods=["GET", "POST"])
def predictions():
    logging.info("🔁 /predictions endpoint hit")
    
    config_path = get_data_source_config_path(g.project_id)
    try:
        with config_path.open() as f:
            config = json.load(f)
    except Exception as e:
        logging.error(f"❌ Failed to load config: {e}")
        return "Server error: cannot load config.", 500

    try:
        target = config['target_variable']
        identifier = config['identifier']
        sensitive = set(config['sensitive_columns'])
    except KeyError as e:
        logging.error(f"❌ Missing key in config: {e}")
        return "Invalid config file.", 500

    all_features = set()
    for source_fields in config['data_sources'].values():
        all_features.update(source_fields.keys())
    valid_features = sorted(all_features - sensitive - {identifier, target})

    model_config_dir = get_model_config_dir(g.project_id)
    model_config_dir.mkdir(parents=True, exist_ok=True)

    try:
        existing_models = [f.stem for f in model_config_dir.glob("*.json")]
    except Exception as e:
        logging.error(f"❌ Failed to read model config dir: {e}")
        existing_models = []

    if request.method == "POST":
        model_name = request.form.get("model_name")
        selected = request.form.getlist("selected_features")

        if not selected:
            return render_template("predictions.html", features=valid_features, existing_models=existing_models, error="Please select at least one feature.")

        model_config = {
            'model_name': model_name,
            'features': selected,
            'target': target
        }

        config_output_path = get_model_config_path(g.project_id, model_name)
        try:
            with config_output_path.open("w") as f:
                json.dump(model_config, f, indent=4)
        except Exception as e:
            logging.error(f"❌ Failed to save model config: {e}")
            return "Error saving model config.", 500

        try:
            df = getFeatures(columns=selected, model_name=model_name)
            train_model(df, model_name=model_name)
        except Exception as e:
            logging.error(f"❌ Model training failed: {e}")
            return f"Model training failed: {e}", 500

        return render_template("predictions.html", features=valid_features, existing_models=existing_models, model_name=model_name, message=f"✅ Model '{model_name}' trained successfully!", data_form="predictions")

    return render_template("predictions.html", features=valid_features, existing_models=existing_models, data_form="predictions")


@prediction_bp.route("/predict/<model_name>", methods=["GET", "POST"])
def predict_page(model_name):
    if request.method == "POST":
        file = request.files.get("predict_file")
        if not file:
            return "No file uploaded.", 400

        temp_file_path = get_temp_upload_path(g.project_id, file.filename)
        temp_file_path.parent.mkdir(parents=True, exist_ok=True)
        file.save(temp_file_path)

        try:
            predictions = makePreds(model_name, temp_file_path)
            user_data = pd.read_csv(temp_file_path)
            if len(predictions) != len(user_data):
                return "Mismatch between number of predictions and input data.", 500
            user_data["Prediction"] = predictions
            return render_template("prediction_results.html", table=user_data.to_html(classes="table table-striped"))
        except Exception as e:
            return f"An error occurred: {str(e)}", 500
        finally:
            temp_file_path.unlink(missing_ok=True)

    return render_template("predict_upload.html", model_name=model_name)

