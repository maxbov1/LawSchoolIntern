import mysql.connector
import pandas as pd
import os
import logging
import json
from .db_helper import connect_project_db
from flask import g
from utils.path_helper import get_model_config_path


def getFeatures(columns=None,model_name="Default"):
    conn = connect_project_db(g.project_id)
    if model_name:
        config_path = get_model_config_path(g.project_id, model_name)
        if not config_path.exists():
            raise FileNotFoundError(f"Model config not found at {config_path}")
        with open(config_path) as f:
            model_config = json.load(f)
        target = model_config["target"]
    else:
        raise ValueError("model_name must be provided to getFeatures()")


    quoted_columns = [f"`{col}`" for col in columns + [target]] if columns else ["*"]
    col_str = ", ".join(quoted_columns)

    query = f"""
    SELECT {col_str} FROM features
    WHERE {target} IS NOT NULL;
    """

    try:
        df = pd.read_sql(query, conn)
        return df
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return pd.DataFrame()
    finally:
        conn.close()

