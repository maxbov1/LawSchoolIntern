import logging
import pandas as pd
import mysql.connector
import os
import numpy as np
from utils.config_loader import load_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def db_connect():
    """ Establishes a connection to the MySQL database. """
    try:
        conn = mysql.connector.connect(
            host="database-barsuccess.c12a2mg6q8ex.us-west-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("pwrd"),
            database="BarSuccess"
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
    if not config or category not in config.data_sources:
        logging.error(f"❌ Invalid category: {category}")
        return

    identifier = config.identifier
    sensitive_columns = config.sensitive_columns

    has_sens_column = any(col in df.columns for col in sensitive_columns)
    # Sanitize SID values and ensure they are strings with leading zeros
    df[identifier] = df[identifier].astype(str).str.zfill(8).str.strip()

    # Convert numeric columns explicitly
    for col in df.columns:
        if col != identifier and df[col].dtype != 'object':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Replace NaN with None after enforcing correct data types
    df = df.where(pd.notnull(df), None)

    # Log the cleaned data before splitting
    logging.info(f"Cleaned data before splitting:\n{df.head()}")
    logging.info(f"Data types after cleaning: {df.dtypes}")

    # Extract sensitive and non-sensitive data (always include the identifier column)
    sensitive_df = df[[identifier] + [col for col in df.columns if col in sensitive_columns]].replace({np.nan: None})
    non_sensitive_df = df[[identifier] + [col for col in df.columns if col not in sensitive_columns and col != identifier]]

    # Check if there are sensitive columns to insert into identity table
    if has_sens_column:
        # Insert/Update identity table only if there are sensitive columns
        identity_data = [tuple(row) for row in sensitive_df.itertuples(index=False, name=None)]
        identity_columns = ", ".join(sensitive_df.columns)
        placeholders = ", ".join(["%s"] * len(sensitive_df.columns))
        query = f"INSERT INTO identity ({identity_columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE " + ", ".join([f"{col} = VALUES({col})" for col in sensitive_df.columns])
        try:
            logging.debug(f"Identity columns: {identity_columns}")
            logging.debug(f"SQL Query: {query}")
            cursor.executemany(query, identity_data)
            conn.commit()
            logging.info(f"✅ Inserted/Updated {len(identity_data)} rows into identity table.")
        except mysql.connector.Error as err:
            logging.error(f"❌ Error inserting/updating identity table: {err}")
    
    # Always retrieve valid SIDs from the identity table before updating features
    try:
        cursor.execute("SELECT SID FROM identity")
        valid_sids = {row[0] for row in cursor.fetchall()}
        logging.info(f"✅ Retrieved {len(valid_sids)} valid SIDs from identity.")
    except mysql.connector.Error as err:
        logging.error(f"❌ Error fetching valid SIDs from identity: {err}")
        valid_sids = set()

    # Filter the non-sensitive dataframe to only include valid SIDs
    filtered_non_sensitive_df = non_sensitive_df[non_sensitive_df[identifier].isin(valid_sids)]
    logging.info(f"✅ Filtered non-sensitive dataframe with valid SIDs. Rows to update: {len(filtered_non_sensitive_df)}")

    # Prepare update data for features table
    update_data = []
    for _, row in filtered_non_sensitive_df.iterrows():
        sid = row[identifier]
        feature_values = tuple(None if pd.isna(row[col]) else row[col] for col in filtered_non_sensitive_df.columns if col != identifier)
        data_tuple = (sid,) + feature_values
        update_data.append(data_tuple)

    logging.info(f"Number of records to update: {len(update_data)}")
    
    if update_data:
        feature_columns = ", ".join([f"`{col}`" if " " in col else col for col in filtered_non_sensitive_df.columns if col != identifier])
        # Construct the final query with VALUES() function for updates
        update_columns = ", ".join([f"`{col}` = VALUES(`{col}`)" if " " in col else f"{col} = VALUES({col})" for col in filtered_non_sensitive_df.columns if col != identifier])
        placeholders = ", ".join(["%s"] * (len(filtered_non_sensitive_df.columns) - 1))  

        # Construct the final query
        query = f"INSERT INTO features ({identifier}, {feature_columns}) VALUES (%s, {placeholders}) " \
                f"ON DUPLICATE KEY UPDATE {update_columns};"
        logging.info(f"Generated Query: {query}")
        

        sample_record = update_data[0] if update_data else None
        logging.info(f"Sample Record: {sample_record}")
        logging.info(f"Number of placeholders: {len(placeholders.split(','))}")
        logging.info(f"Number of values in sample record: {len(sample_record)}")
        logging.info(f"Expected placeholders: {len(filtered_non_sensitive_df.columns)}")
        
        try:
            cursor.executemany(query, update_data)
            conn.commit()
            logging.info(f"✅ Successfully processed {len(update_data)} feature records.")
        except mysql.connector.Error as err:
            logging.error(f"❌ Error inserting/updating features table: {err}")
    else:
        logging.info(f"⚠️ No records processed for features.")


    cursor.close()
    conn.close()

