import json
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler
from flask import g
from utils.path_helper import get_model_config_path, get_model_config_dir

def makePreds(model_name, user_csv_file):
    # Get paths using helpers
    config_path = get_model_config_path(g.project_id, model_name)
    model_dir = get_model_config_dir(g.project_id)
    model_path = model_dir / f"{model_name}.pkl"

    # Load model config
    with config_path.open() as f:
        model_config = json.load(f)

    expected_features = model_config.get("features")
    if not expected_features:
        raise ValueError("Model config is missing the 'features' list.")

    target = model_config.get("target")
    preprocessing_steps = model_config.get("preprocessing", {})

    # Load trained model
    model = joblib.load(model_path)

    # Load and prepare user data
    user_data = pd.read_csv(user_csv_file)

    # Optionally rename columns if needed (this should eventually be dynamic)
    user_data.columns = ['law_gpa', 'Applicant GPA', 'LSAT']

    # Align user data to model input
    user_data = user_data[expected_features]

    # Apply preprocessing if needed (placeholder)
    if preprocessing_steps.get("scale", True):
        scaler = StandardScaler()
        user_data = scaler.fit_transform(user_data)

    predictions = model.predict(user_data)
    return predictions

