import os
import json
import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from flask import g
from utils.path_helper import get_model_config_path, get_model_config_dir
import logging


def train_model(df, model_name="default"):
    # Load model config
    config_path = get_model_config_path(g.project_id, model_name)
    logging.error(f" model config path : {config_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"Model config not found at {config_path}")

    with config_path.open() as f:
        model_config = json.load(f)

    selected_features = model_config["features"]
    target = model_config["target"]

    df.dropna(subset=selected_features + [target], inplace=True)

    # Encode binary target if necessary
    if df[target].dtype == object or df[target].nunique() <= 2:
        df.loc[df[target] == 'PASS', target] = 1
        df.loc[df[target] != 1, target] = 0
        df[target] = df[target].astype(int)

    X = df[selected_features]
    y = df[target]

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train pruned Decision Tree
    model = DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=10,
        ccp_alpha=0.005,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluation (can be removed or logged)
    print("✅ Training complete")
    print(classification_report(y_test, model.predict(X_test)))

    # Save model
    
    model_dir = get_model_config_dir(g.project_id)
    model_dir.mkdir(parents=True, exist_ok=True)
    logging.error(f"model dir = {model_dir}")
    model_path = model_dir / f"{model_name}.pkl"
    joblib.dump(model, model_path)
    
    print(f"✅ Model saved to {model_path}")

