import logging
import pandas as pd
import mysql.connector
import os
import numpy as np

def db_connect():
    """
    Establishes a connection to the MySQL database.
    Returns a connection object if successful, otherwise prints an error and returns None.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv("pwrd"),
            database="law_students_db"
        )
        return conn
    except mysql.connector.Error as err:
        logging.info(f"Error: {err}")
        return None

def insert_data(df, category):
    """
    Inserts records from the structured DataFrame into the appropriate tables.
    Each category expects a different DataFrame structure.
    """
    conn = db_connect()
    if conn is None:
        return

    cursor = conn.cursor()

    logging.info(f" dataframe before insert : \n{df.head()} ")

    if category == 'additional':
        query = """
INSERT INTO additional (SID, bar_review, review_completion)
SELECT df.SID, df.bar_review, df.review_completion
FROM (
    SELECT %s AS SID, %s AS bar_review, %s AS review_completion
) AS df
INNER JOIN identity i ON df.SID = i.SID;
"""
        expected_columns = ["SID", "bar_review", "review_completion"]

    elif category == 'registrar':
        query_identity = """
        INSERT INTO identity (SID, last_name, first_name, grad_date, jd_level)
        VALUES (%s, %s, %s, %s, %s)
        """
        query_academics = """
        INSERT INTO academics (SID, cumulative_gpa)
        VALUES (%s, %s)
        """
        expected_columns = ["SID", "last_name", "first_name", "grad_date", "jd_level", "cumulative_gpa"]

    elif category == 'admissions':
        query_identity = """
INSERT INTO identity (SID, lastname, firstname)
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE 
    lastname = VALUES(lastname),
    firstname = VALUES(firstname);
        """
        query_academics = """
INSERT INTO academics (SID, undergrad_gpa, lsat_score)
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE 
    undergrad_gpa = VALUES(undergrad_gpa),
    lsat_score = VALUES(lsat_score);
        """

        expected_columns = ["SID", "lastname", "firstname", "undergrad_gpa", "lsat_score"]

    else:
        logging.info("Invalid category. Please choose 'additional', 'registrar', or 'admissions'.")
        return
    df = df[expected_columns]
    df = df.replace({np.nan: None})
    
    logging.info(f"rows with nans : {df[df.isna().any(axis=1)]}")

    if list(df.columns) != expected_columns:
        logging.info(f"Error: Expected columns {expected_columns}, but got {list(df.columns)}")
        return
    try:
        for _, row in df.iterrows():
            if category == 'admissions':
                identity_data = (row["SID"], row["lastname"], row["firstname"])
                academics_data = (row["SID"], row["undergrad_gpa"], row["lsat_score"])

                cursor.execute(query_identity, identity_data)
                cursor.execute(query_academics, academics_data)
            else:
                cursor.execute(query, tuple(row))

        conn.commit()
        logging.info(f"Data inserted into {category} table successfully.")

    except mysql.connector.Error as err:
        logging.info(f"Error :) : {err}")
        conn.rollback()

    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()

