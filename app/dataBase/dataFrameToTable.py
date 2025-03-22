import logging
import pandas as pd
import mysql.connector
import os
import numpy as np
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_PATH = 'config/data_source_config.json'

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return None


def db_connect():
    """ Establishes a connection to the MySQL database. """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv("pwrd"),
            database="law_studs"
        )
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Database Connection Error: {err}")


def insert_data(df, category):
    """ Inserts data into the MySQL database based on the category. """
    conn = db_connect()
    if conn is None:
        return
    cursor = conn.cursor()

    config = load_config()
    if not config or category not in config['data_sources']:
        logging.error(f"❌ Invalid category: {category}")
        return

    identifier = config.get("identifier", "SID")
    sensitive_columns = config.get("sensitive_columns", [])

    # Sanitize SID values
    df[identifier] = df[identifier].astype(str).str.strip()

    # Extract sensitive and non-sensitive data (always include the identifier column)
    sensitive_df = df[[col for col in df.columns if col in sensitive_columns or col == identifier]].replace({np.nan: None})
    non_sensitive_df = df[[identifier] + [col for col in df.columns if col not in sensitive_columns and col != identifier]].replace({np.nan: None})


    # Insert/Update identity table
    identity_data = [tuple(row) for row in sensitive_df.itertuples(index=False, name=None)]
    identity_columns = ", ".join(sensitive_df.columns)
    placeholders = ", ".join(["%s"] * len(sensitive_df.columns))
    query = f"INSERT INTO identity ({identity_columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE " + ", ".join([f"{col} = VALUES({col})" for col in sensitive_df.columns])
    cursor.executemany(query, identity_data)
    conn.commit()
    logging.info(f"✅ Inserted/Updated {len(identity_data)} rows into identity table.")

    # Ensure that non-sensitive data is only processed if SID exists in identity
    cursor.execute("SELECT SID FROM identity")
    valid_sids = {row[0] for row in cursor.fetchall()}
    logging.info(f"✅ Retrieved {len(valid_sids)} valid SIDs from identity.")
    logging.info(f"Columns in non_sensitive_df: {non_sensitive_df.columns.tolist()}")
    logging.info(f"Data types in non_sensitive_df: {non_sensitive_df.dtypes}")

    update_data = []
    for _, row in non_sensitive_df.iterrows():
        sid = row[identifier]
        if sid not in valid_sids:
            logging.warning(f"⚠️ Skipping SID {sid}: Not found in identity table.")
            continue
        # Extract the feature values only (excluding SID)
        feature_values = tuple(row[col] for col in non_sensitive_df.columns if col != identifier)
        update_data.append((sid,) + feature_values)

    if update_data:
        # Exclude the identifier from feature columns as it is used separately
        feature_columns = ", ".join([col for col in non_sensitive_df.columns if col != identifier])
        placeholders = ", ".join(["%s"] * (len(non_sensitive_df.columns) - 1))  # Subtract 1 for SID
        update_columns = ", ".join([f"{col} = VALUES({col})" for col in non_sensitive_df.columns if col != identifier])

        # Construct the final query
        query = f"INSERT INTO features ({identifier}, {feature_columns}) VALUES (%s, {placeholders}) " \
                f"ON DUPLICATE KEY UPDATE {update_columns};"
        logging.info(f"Generated Query: {query}")

        # Execute the batch update
        cursor.executemany(query, update_data)
        conn.commit()
        logging.info(f"✅ Successfully processed {len(update_data)} feature records.")
    else:
        logging.info(f"⚠️ No records processed for features.")

    # Close the cursor and connection
    cursor.close()
    conn.close()

