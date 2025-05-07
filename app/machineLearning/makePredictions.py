import os
import json
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler  # Adjust based on actual preprocessing used
from flask import g

def makePreds(model_name, user_csv_file):
    config_path = os.path.join("config", f"project_{g.project_id}", "model_configs", f"{model_name}.json")
    model_path = os.path.join("models", f"project_{g.project_id}", f"{model_name}.pkl")

    with open(config_path, 'r') as f:
        model_config = json.load(f)

    target = model_config.get("target")
    preprocessing_steps = model_config.get("preprocessing", {})

    model = joblib.load(model_path)

    user_data = pd.read_csv(user_csv_file)
    user_data.columns = ['law_gpa','Applicant GPA', 'LSAT']

    expected_features = model_config.get("features")
    if expected_features:
        user_data = user_data[expected_features]
        scaler = StandardScaler()
        user_data = scaler.fit_transform(user_data)

    predictions = model.predict(user_data)
    return predictions
