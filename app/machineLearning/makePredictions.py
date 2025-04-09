import os
import json
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler  # Adjust based on actual preprocessing used

def makePreds(model_name, user_csv_file):
    # Define paths
    config_path = os.path.join("config", "model_configs", f"{model_name}.json")
    model_path = os.path.join("models", f"{model_name}.pkl")

    # Load model configuration
    with open(config_path, 'r') as f:
        model_config = json.load(f)
    
    # Extract target variable and preprocessing details from config
    target = model_config.get("target")
    preprocessing_steps = model_config.get("preprocessing", {})

    # Load the trained model
    model = joblib.load(model_path)

    # Load the user data
    user_data = pd.read_csv(user_csv_file)
    user_data.columns = ['law_gpa','Applicant GPA', 'LSAT']
    # Ensure the user data has the same features as the training data
    expected_features = model_config.get("features")
    if expected_features:
        user_data = user_data[expected_features]
        scaler = StandardScaler()
        user_data = scaler.fit_transform(user_data)
    # Add other preprocessing steps as needed

    # Make predictions
    predictions = model.predict(user_data)

    return predictions

