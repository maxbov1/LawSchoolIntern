import mysql.connector
import pandas as pd
import os
import logging
import json

def getFeatures(columns=None,model_name="Default"):
    conn = mysql.connector.connect(
        host="database-barsuccess.c12a2mg6q8ex.us-west-1.rds.amazonaws.com",
        user="admin",
        password=os.getenv("pwrd"),
        database="BarSuccess"
    )

    if model_name:
        config_path = os.path.join("config", "model_configs", f"{model_name}.json")
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

