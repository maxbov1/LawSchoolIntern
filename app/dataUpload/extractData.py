import pandas as pd
import numpy as np
import re
import logging
import json
import os

CONFIG_PATH = 'config/data_source_config.json'


def load_config():
    try:
        with open(CONFIG_PATH, 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return None


def extract(category, data, cols=None):
    '''
    This function accepts two arguments: the category or source of the data, and the data (pd.Dataframe).
    This function is responsible for extracting the data in our given CSV based upon pre-defined configurations.
    The function returns a cleaned pandas df indexed on SID.
    '''
    config = load_config()
    if not config or category not in config['data_sources']:
        logging.error(f"Configuration for category '{category}' not found.")
        return None

    try:
        # Get the list of expected columns from the config
        expected_cols = config['data_sources'][category].keys()
        logging.info(f'expected cols : {expected_cols}')
        # Extract only the relevant columns without type conversion or manipulation
        available_cols = [col for col in expected_cols if col in data.columns]
        logging.info(f'data cols :{data.columns}') 
        data = data[available_cols]

        logging.info(f"Extracted columns for {category}: {available_cols}")
        logging.info(f'data before extract : {data.head()}')
        # Keep existing manipulation logic intact
        if category == 'additional':
            try:
                required_columns = ["SID", "bar_review", "review_completion"]
                available_cols = [col for col in required_columns if col in data.columns]
                missing_columns = [col for col in required_columns if col not in data.columns]
                if missing_columns:
                    logging.error(f"Missing columns in 'additional' category: {missing_columns}")
                    return None
                data = data[available_cols]
                extract_first_percent = lambda x: int(re.search(r"(\d+)%", str(x)).group(1)) if re.search(r"(\d+)%", str(x)) else None
                data['review_completion'] = data['review_completion'].apply(extract_first_percent)
                data = data.dropna(subset=["SID"])
                data['SID'] = data['SID'].astype(int).astype(str).str.zfill(8)
                logging.info(f"additional data: {data}")
                logging.info(f"additional dtypes: {data.dtypes}")
                return data
            except Exception as e:
                logging.exception(f"Unexpected error: {e}")

        elif category == 'bar':
            bar_clean = data.loc[:,["SID","result","juris"]]
            bar_clean = bar_clean.dropna(axis=0)
            bar_clean['SID'] = bar_clean['SID'].astype(int).astype(str).str.zfill(8)
            logging.info(f"bar data: {bar_clean}")
            logging.info(f"bar dtypes: {bar_clean.dtypes}")
            return bar_clean

        elif category == 'registrar':
            registrar = data.loc[:, ["law_gpa", "SID", "NetID", "grad_date", "firstname", "lastname"]]
            registrar['SID'] = registrar['SID'].astype(str).str.zfill(8)
            registrar['lastname'] = registrar['lastname'].astype(str).apply(lambda x: ''.join(filter(str.isprintable, x)).strip())

            registrar = registrar.dropna(subset=['SID'])
            logging.info(f"registrar data: {registrar}")
            logging.info(f"Row 643 Data: {registrar.loc[643]}")
            logging.info(f"registrar dtypes: {registrar.dtypes}")
            
            return registrar

        elif category == 'admissions':
            try:
                admissions_cleaned = data.loc[:, ['SID', 'LSAT', 'Applicant GPA']]
                admissions_cleaned.columns = ['SID', 'lsat_score', 'undergrad_gpa']
                admissions_cleaned = admissions_cleaned.dropna(subset=['SID'])
                admissions_cleaned['SID'] = admissions_cleaned['SID'].astype(int).astype(str).str.zfill(8)
                logging.info(f"admissions data: {admissions_cleaned}")
                logging.info(f"admissions dtypes: {admissions_cleaned.dtypes}")
                return admissions_cleaned
            except KeyError as e:
                logging.error(f"Missing column in the data: {e}")
            except Exception as e:
                logging.exception(f"Unexpected error: {e}")

    except Exception as e:
        logging.error(f"Error extracting data for category '{category}': {e}")
        return None

