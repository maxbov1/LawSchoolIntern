import pandas as pd
import plotly.express as px
import json
import os
import logging
from pandas.api.types import is_numeric_dtype
from utils.config_loader import load_config
import random
from itertools import combinations
from flask import g
from dataBase.db_helper import connect_project_db


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
    config = load_config()
    # ✅ Create cache dir per project inside request context
    cache_dir = os.path.join("/tmp/dashboard_charts", f"project_{g.project_id}")
    os.makedirs(cache_dir, exist_ok=True)
    try:
        conn = connect_project_db(g.project_id)
        df = pd.read_sql(f"SELECT * FROM features WHERE {config.target_variable} IS NOT NULL", conn)
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
    df.loc[df['result'] == 'PASS', 'result'] = 1
    df.loc[df['result'] != 1, 'result'] = 0
    df['result'] = df['result'].astype(int)
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
    
    if target in df.columns:
        if df[target].dtype in ['int64', 'float64']:
            # Go through all pairs of features, excluding the target
            for f1, f2 in combinations([f for f in numeric if f != target], 2):
                try:
                    fig = px.scatter(
                        df,
                        x=f1,
                        y=f2,
                        color=df[target].astype(str),  # convert 0/1 to string for distinct hue
                        title=f"{f1} vs {f2} by {target}"
                    )
                    charts.append(fig.to_html(full_html=False))
                    logging.info(f"Generated scatter plot: {f1} vs {f2} by {target}.")
                except Exception as e:
                    logging.warning(f"Failed to generate scatter plot for {f1} vs {f2}: {e}")

    else:
        logging.warning(f"Target variable '{target}' not found in dataframe.")
    random.shuffle(charts)
    cached_chart_paths = []

    for idx, html in enumerate(charts):   
        cache_path = os.path.join(cache_dir, f"chart_{idx}.html")
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(html)
        cached_chart_paths.append(f"/chart/{idx}")

    return cached_chart_paths
