import pandas as pd
import plotly.express as px
import json
import os
import logging
from dataBase.dbBuilder import db_connect
from pandas.api.types import is_numeric_dtype
from utils.config_loader import load_config
import random

CONFIG_PATH = os.path.join("config", "data_source_config.json")
CACHE_DIR = "/tmp/dashboard_charts"
os.makedirs(CACHE_DIR, exist_ok=True)

def classify_features(df, feature_list):
    numeric = []
    categorical = []
    for col in feature_list:
        if col in df.columns:
            if is_numeric_dtype(df[col]):
                numeric.append(col)
            else:
                categorical.append(col)
    logging.info(f"Classified {len(numeric)} numeric and {len(categorical)} categorical features.")
    return numeric, categorical

def generate_charts():
    charts = []

    try:
        conn = db_connect()
        df = pd.read_sql("SELECT * FROM features WHERE result IS NOT NULL", conn)
        conn.close()
        logging.info("Successfully loaded data from database.")
    except Exception as e:
        logging.error(f"Error loading data from database: {e}")
        return charts
    
    config = load_config()

    # Dynamically build the features list
    exclude = {config.identifier, config.target_variable, *config.sensitive_columns}
    features = []

    for source_fields in config.data_sources.values():
        for col in source_fields.keys():
            if col not in exclude and col not in features:
                features.append(col)

    target = config.target_variable
    logging.info(f"features: {features}, target: {target}")

    numeric, categorical = classify_features(df, features)
    logging.info(f"Numeric features: {numeric}")
    logging.info(f"Categorical features: {categorical}")
    
    for feature in numeric:
        try:
            fig = px.histogram(df, x=feature, title=f"Distribution of {feature}")
            charts.append(fig.to_html(full_html=False))
            logging.info(f"Generated histogram for {feature}.")
        except Exception as e:
            logging.warning(f"Failed to generate histogram for {feature}: {e}")

    for feature in categorical:
        try:
            grouped = df[feature].value_counts().reset_index()
            grouped.columns = [feature, 'count']
            fig = px.bar(grouped, x=feature, y='count', title=f"Counts of {feature}")
            charts.append(fig.to_html(full_html=False))
            logging.info(f"Generated bar chart for {feature}.")
        except Exception as e:
            logging.warning(f"Failed to generate bar chart for {feature}: {e}")

    if target in df.columns:
        if df[target].dtype in ['int64', 'float64']:
            for feature in numeric:
                if feature != target:
                    try:
                        fig = px.scatter(df, x=feature, y=target, title=f"{feature} vs {target}")
                        charts.append(fig.to_html(full_html=False))
                        logging.info(f"Generated scatter plot: {feature} vs {target}.")
                    except Exception as e:
                        logging.warning(f"Failed to generate scatter plot for {feature} vs {target}: {e}")
    else:
        logging.warning(f"Target variable '{target}' not found in dataframe.")
    random.shuffle(charts)
    cached_chart_paths = []

    for idx, html in enumerate(charts):   
        cache_path = os.path.join(CACHE_DIR, f"chart_{idx}.html")
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(html)
        cached_chart_paths.append(f"/chart/{idx}")

    return cached_chart_paths
