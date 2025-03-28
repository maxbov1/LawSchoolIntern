import mysql.connector
import pandas as pd
import os
import logging

def getFeatures():
    conn = mysql.connector.connect(
        host="database-barsuccess.c12a2mg6q8ex.us-west-1.rds.amazonaws.com",
        user="admin",
        password=os.getenv("pwrd"),
        database="BarSuccess"
    )

    query = """
    SELECT * FROM features
    WHERE result IS NOT NULL;
    """

    try:
        # Use pandas to read the SQL query directly into a DataFrame
        df = pd.read_sql(query, conn)
        print(df)
        return df

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return pd.DataFrame()

    finally:
        conn.close()


