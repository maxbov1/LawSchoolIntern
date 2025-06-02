import pandas as pd
import numpy as np
import re
import logging
import json
import os
from utils.dynamic_models import create_dynamic_model
from pydantic import ValidationError
from utils.config_loader import load_config


def extract(category, data, cols=None):
    '''
    This function accepts two arguments: the category or source of the data, and the data (pd.DataFrame).
    It processes and cleans the data according to category-specific rules, and returns the cleaned but not yet validated dataframe (`invalidated_df`).
    '''
    try:
        # Step 1: Dynamically create the Pydantic model for this category
        model = create_dynamic_model(category)

        # Step 2: Get expected columns dynamically from model fields
        expected_cols = model.__annotations__.keys()
        logging.info(f'Expected columns: {expected_cols}')

        # Extract relevant columns without type conversion or manipulation
        data.columns = data.columns.str.strip()
        available_cols = [col for col in expected_cols if col in data.columns]
        data = data[available_cols]
        logging.info(f"Extracted columns for {category}: {available_cols}")

        # Now the cleaned data is referred to as 'invalidated_df' to indicate that it is not validated yet
        invalidated_df = data.copy()

        # Step 3: Category-Specific Processing (Preserve Original Logic)
        if category == 'additional':
            try:
                extract_first_percent = lambda x: int(re.search(r"(\d+)%", str(x)).group(1)) if re.search(r"(\d+)%", str(x)) else None
                invalidated_df['review_completion'] = invalidated_df['review_completion'].apply(extract_first_percent)

                invalidated_df = invalidated_df.dropna(subset=["SID"])
                invalidated_df['SID'] = invalidated_df['SID'].astype(int).astype(str).str.zfill(8)

            except Exception as e:
                logging.exception(f"Unexpected error processing 'additional' category: {e}")

        elif category == 'bar':
            try:
                bar_clean = invalidated_df.dropna(subset=['SID'])

                # Clean SID
                bar_clean['SID'] = bar_clean['SID'].astype(int).astype(str).str.zfill(8)

                return bar_clean

            except Exception as e:
                logging.exception(f"Unexpected error processing 'bar' category: {e}")

        elif category == 'registrar':
            try:
                registrar = invalidated_df.dropna(subset=['SID'])
                registrar['SID'] = registrar['SID'].astype(str).str.zfill(8)
                registrar['lastname'] = registrar['lastname'].astype(str).apply(lambda x: ''.join(filter(str.isprintable, x)).strip())

                return registrar

            except Exception as e:
                logging.exception(f"Unexpected error processing 'registrar' category: {e}")

        elif category == 'admissions':
            try:
                #invalidated_df.columns = ['SID', 'lsat_score', 'undergrad_gpa']
                admissions_cleaned = invalidated_df
                admissions_cleaned = admissions_cleaned.dropna(subset=['SID'])

                # Clean SID
                admissions_cleaned.loc[:, 'SID'] = admissions_cleaned['SID'].astype(int).astype(str).str.zfill(8)
                return admissions_cleaned

            except Exception as e:
                logging.exception(f"Unexpected error processing 'admissions' category: {e}")

        return invalidated_df

    except Exception as e:
        logging.error(f"Error extracting data for category '{category}': {e}")
        return None


def typeConvert(data, category):
    '''
    This function takes the cleaned dataframe and converts each column to its expected type
    based on the category's model annotations. If conversion fails for a column, it will be skipped.
    '''
    try:
        model = create_dynamic_model(category)

        expected_cols = model.__annotations__.keys()
        expected_types = model.__annotations__.values()

        type_dict = {}
        for col, col_type in zip(expected_cols, expected_types):
            if col in data.columns:
                if col_type == str:
                    type_dict[col] = 'string'  # pandas 'string' type
                elif col_type == int:
                    type_dict[col] = 'int32'
                elif col_type == float:
                    type_dict[col] = 'float64'
                elif col_type == bool:
                    type_dict[col] = 'bool'
        
        data = data.astype(type_dict)

        logging.info(f"Data after type conversion: {data.dtypes}")
        return data

    except Exception as e:
        logging.error(f"Error during type conversion for category '{category}': {e}")
        return None

def validateData(df, category):
    """
    Validates the DataFrame using the dynamically created Pydantic model.
    Returns the validated data or None if validation fails.
    """
    try:
        # Replace NaN values with None
        df = df.where(pd.notnull(df), None)
        
        model = create_dynamic_model(category)
        validated_data = []

        for index, row in df.iterrows():
            try:
                validated_row = model.parse_obj(row.to_dict())
                validated_data.append(validated_row.dict())
            except ValidationError as e:
                logging.error(f"Validation error for row {index} in category '{category}': {e}")
                continue  # Skip this row and move to the next

        validated_df = pd.DataFrame(validated_data)
        return validated_df

    except Exception as e:
        logging.error(f"Error during validation for category '{category}': {e}")
        return None

