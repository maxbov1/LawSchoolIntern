import pandas as pd
from dataUpload.extractData import extract, typeConvert, validateData
from dataBase.dataFrameToTable import insert_data
import os
from dataBase.encrypt import encrypt_dataframe, decrypt_dataframe, encrypt_value
import logging
import json
from utils.config_loader import load_config  


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
    data_sources = config.data_sources
    sensitive_columns = config.sensitive_columns
    if not config or category not in config.data_sources:
        raise ValueError(f"Invalid category '{category}' or missing configuration.")
    
    try:
        # Read the CSV file
        df = pd.read_csv(filepath, encoding='latin-1')
        logging.debug(f"Category received: {category}")

        invalidated_df = extract(category=category, data=df)
        if invalidated_df is None:
            raise ValueError(f"Failed to extract or validate data for category: {category}")
        else:
            logging.info(f"extracted {category} data : {invalidated_df.head(10)}")
        typed_df = typeConvert(invalidated_df, category)  # Convert types
        if typed_df is None:
            raise ValueError(f"Type conversion failed for data in category: {category}")
            
        try: 
            validated_df = validateData(typed_df, category)  # Validate data here
            if validated_df is None:
                raise ValueError(f"Validation failed for data in category: {category}")
            else:
                logging.info(f"{category} data successfully passed validation")
        except Exception as validation_error:
            return f"Error: Validation failed for category '{category}': {validation_error}"
        
        # Step 2: Dynamically encrypt sensitive data based on configuration
        if sensitive_columns:
            logging.info(f"Sensitive columns for {category}: {sensitive_columns}")

            # Check if sensitive columns exist in the current DataFrame (typed_df)
            existing_sensitive_cols = [col for col in sensitive_columns if col in typed_df.columns]
            if existing_sensitive_cols:
                logging.info(f"Found sensitive columns in the data: {existing_sensitive_cols}")
                validated_df = encrypt_dataframe(validated_df, existing_sensitive_cols, os.getenv("genkey"))
            else:
                logging.warning(f"No sensitive columns found in the data for category '{category}'.")

        # Step 3: Insert data into the database
        inserted = insert_data(validated_df, category)

        return f"File processed successfully under the category: {category}"
    
    except ValueError as e:
        logging.error(f"Error: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logging.error(f"Error processing CSV for category '{category}': {e}")
        return f"Error processing file: {str(e)}"

