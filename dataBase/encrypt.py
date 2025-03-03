from cryptography.fernet import Fernet
import pandas as pd

def encrypt_value(value, cipher):
    if pd.isna(value):  
        return value
    return cipher.encrypt(value.encode()).decode()

def decrypt_value(value, cipher):
    if pd.isna(value):
        return value
    return cipher.decrypt(value.encode()).decode()

def encrypt_dataframe(df, gk):
    '''
    this function accepts the admissions dataframe, and a generated key. The function returns the df with fields "firstname" and "lastname" encrypted.

    '''
    cipher = Fernet(gk)  
    df['firstname'] = df['firstname'].apply(lambda x: encrypt_value(x, cipher))
    df['lastname'] = df['lastname'].apply(lambda x: encrypt_value(x, cipher))
    return df

def decrypt_dataframe(df, gk):
    '''
    this function accepts an ecrypted admissions dataframe, and the generated key. It returns the decrypted dataframe.

    '''
    cipher = Fernet(gk) 
    df['firstname'] = df['firstname'].apply(lambda x: decrypt_value(x, cipher))
    df['lastname'] = df['lastname'].apply(lambda x: decrypt_value(x, cipher))
    return df

def gen_key():
    '''
    this function takes no args and generates the key responsible for encrypting the admissions dataframe. 

    '''
    key = Fernet.generate_key()
    print(f"Your encryption key : {key.decode()}")
