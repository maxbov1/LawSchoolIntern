import pandas as pd
from .extractData import extract
from dataBase.dataFrameToTable import db_connect, insert_data
import os
from dataBase.encrypt import encrypt_dataframe, decrypt_dataframe
import logging


def allowed_file(filename, allowed_extensions):
    """Check if the uploaded file is a CSV."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def process_csv(filepath, category):
    """
    Process the CSV file based on the selected category.

    Args:
        filepath (str): The path to the saved CSV file.
        category (str): The selected category ("additional", "registrar", or "admissions").

    Returns:
        str: Success message.
    """
    # Read the CSV file
    df = pd.read_csv(filepath, encoding='latin-1')
    logging.debug(f"Category received: {category}")
    # Process based on category
    if category == 'additional':
        clean = extract(cols=["","",""],category='additional',data=df) 
        inserted = insert_data(clean,category='additional')    

    elif category == 'registrar':
        clean = extract(category='registrar',data=df)
        genkey = os.getenv("genkey")
        encrypted = encrypt_dataframe(clean,genkey)
        logging.info(f'encrypted_df : encrypted')
        inserted = insert_data(encrypted,category='registrar')
    elif category == 'bar':
        logging.debug(f"bar category selected")
        clean = extract(category='bar',data=df)
        logging.debug(f"bar data cleaned : {clean}")
        inserted = insert_data(clean, category='bar')

    elif category == 'admissions':
        clean = extract(category='admissions',data=df)
        inserted = insert_data(clean,category='admissions')
    else:
        raise ValueError("Invalid category provided")
    
    return f"File processed successfully under the category: {category}"

