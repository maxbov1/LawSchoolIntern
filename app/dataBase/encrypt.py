from cryptography.fernet import Fernet
import pandas as pd
import logging
from utils.config_loader import load_config

def encrypt_value(value, cipher):
    if pd.isna(value):  
        return value
    return cipher.encrypt(value.encode()).decode()

def decrypt_value(value, cipher):
    if pd.isna(value):
        return value
    return cipher.decrypt(value.encode()).decode()

def encrypt_dataframe(df, sensitive_columns, gk):
    '''
    This function accepts a dataframe, a list of sensitive columns, and a generated key.
    It returns the dataframe with sensitive fields encrypted.
    '''
    cipher = Fernet(gk) 

    # Iterate over all sensitive columns in the list and encrypt each
    for col in sensitive_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: encrypt_value(x, cipher))
            logging.info(f"Encrypted column '{col}'")
        else:
            logging.warning(f"Sensitive column '{col}' not found in dataframe, skipping encryption.")

    return df

def decrypt_column(df, column, gk):
    cipher = Fernet(gk)
    df[column] = df[column].apply(lambda x: decrypt_value(x, cipher))
    return df



def decrypt_dataframe(df,sensitive_columns,gk):
    '''
    this function accepts an ecrypted admissions dataframe, and the generated key. It returns the decrypted dataframe.

    '''
    cipher = Fernet(gk) 
    for col in sensitive_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: decrypt_value(x, cipher))
            logging.info(f"Decrypted column '{col}'")
        else:
            logging.warning(f"Sensitive column '{col}' not found in dataframe, skipping decryption.")

    return df

def gen_key():
    '''
    this function takes no args and generates the key responsible for encrypting the admissions dataframe. 

    '''
    key = Fernet.generate_key()
    print(f"Your encryption key : {key.decode()}")
