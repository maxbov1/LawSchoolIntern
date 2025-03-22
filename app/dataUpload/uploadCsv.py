import pandas as pd
from .extractData import extract
from dataBase.dataFrameToTable import db_connect, insert_data
import os
from dataBase.encrypt import encrypt_dataframe, decrypt_dataframe
import logging
import json

CONFIG_PATH = 'config/data_source_config.json'


def load_config():
    try:
        with open(CONFIG_PATH, 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return None


def allowed_file(filename, allowed_extensions):
    """Check if the uploaded file is a CSV."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def process_csv(filepath, category):
    """
    Process the CSV file based on the selected category.

    Args:
        filepath (str): The path to the saved CSV file.
        category (str): The selected category.

    Returns:
        str: Success message.
    """
    # Load the configuration
    config = load_config()
    if not config or category not in config['data_sources']:
        raise ValueError(f"Invalid category '{category}' or missing configuration.")

    # Read the CSV file
    df = pd.read_csv(filepath, encoding='latin-1')
    logging.debug(f"Category received: {category}")

    # Extract the cleaned data dynamically
    clean = extract(category=category, data=df)
    if clean is None:
        raise ValueError(f"Failed to extract data for category: {category}")

    # Encrypt data if necessary
    if category == 'registrar':
        genkey = os.getenv("genkey")
        encrypted = encrypt_dataframe(clean, genkey)
        logging.info(f'encrypted_df : {encrypted}')
        inserted = insert_data(clean, category)
    else:
        inserted = insert_data(clean, category)

    return f"File processed successfully under the category: {category}"

