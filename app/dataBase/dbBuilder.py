import mysql.connector
import os
import json
import logging

CONFIG_PATH = 'config/data_source_config.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    try:
        logging.info(f"🔄 Attempting to load configuration from {CONFIG_PATH}")
        with open(CONFIG_PATH, 'r') as file:
            config = json.load(file)
            logging.info("✅ Configuration loaded successfully")
            return config
    except Exception as e:
        logging.error(f"❌ Error loading configuration: {e}")
        return None

def db_connect():
    try:
        logging.info("🔄 Attempting to connect to the database...")
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv("pwrd"),
            database="law_studs"
        )
        logging.info("✅ Database connection established")
        return conn
    except mysql.connector.Error as err:
        logging.error(f"❌ Database Connection Error: {err}")
        return None

def create_table(query):
    logging.info(f"🔧 Executing table creation query: {query}")
    conn = db_connect()
    if conn is None:
        logging.error("❌ No database connection available.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        logging.info("✅ Table created successfully.")
    except mysql.connector.Error as err:
        logging.error(f"❌ Error creating table: {err}")
    finally:
        cursor.close()
        conn.close()
        logging.info("🔒 Database connection closed.")
def build_db():
    logging.info("🚀 Starting database build process.")
    config = load_config()
    if not config:
        logging.error("❌ Configuration not found.")
        return

    # Identity Table Creation
    identifier = config.get("identifier", "SID")
    sensitive_columns = config.get("sensitive_columns", [])
    logging.info(f"🔑 Identifier: {identifier}")
    logging.info(f"🔒 Sensitive columns: {sensitive_columns}")

    identity_cols = [f"`{identifier}` VARCHAR(50) PRIMARY KEY"] + [f"`{col}` VARCHAR(255)" for col in sensitive_columns]
    identity_query = f"CREATE TABLE IF NOT EXISTS identity ({', '.join(identity_cols)});"
    logging.info(f"🔨 Preparing identity table with columns: {identity_cols}")
    create_table(identity_query)

    # Features Table Creation
    feature_cols = [f"`{identifier}` VARCHAR(50) PRIMARY KEY"]
    added_features = set()

    for source_name, details in config['data_sources'].items():
        logging.info(f"📂 Processing data source: {source_name}")
        for feature_name, dtype in details.items():
            if feature_name not in sensitive_columns and feature_name != identifier:
                if feature_name not in added_features:
                    sql_type = "TEXT" if dtype == "string" else "FLOAT"
                    logging.info(f"📑 Adding feature: {feature_name} with type: {sql_type}")
                    feature_cols.append(f"`{feature_name}` {sql_type}")
                    added_features.add(feature_name)

    features_query = f"CREATE TABLE IF NOT EXISTS features ({', '.join(feature_cols)});"
    logging.info(f"🔧 Preparing features table with columns: {feature_cols}")
    create_table(features_query)

    logging.info("✅ Database build process completed successfully.")

