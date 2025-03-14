import logging
import pandas as pd
import mysql.connector
import os
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def db_connect():
    """ Establishes a connection to the MySQL database. """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv("pwrd"),
            database="law_students_db"
        )
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Database Connection Error: {err}")
        return None

def insert_data(df, category):
    """ Inserts data into the MySQL database based on the category. """
    conn = db_connect()
    if conn is None:
        return
    
    cursor = conn.cursor()
    pd.set_option('display.max_columns', None)

    logging.info(f"📌 DataFrame before insert ({category}):\n{df.head(10)}")  # Show first 10 rows

    # Define expected columns per category
    category_columns = {
        "registrar": ["SID", "lastname", "firstname", "NetID", "grad_date", "law_gpa"],
        "admissions": ["SID", "undergrad_gpa", "lsat_score"],
        "additional": ["SID", "bar_review", "review_completion"],
        "bar": ["SID", "result", "juris"]
    }

    if category not in category_columns:
        logging.error(f"❌ Invalid category: {category}")
        return

    expected_columns = category_columns[category]

    # Ensure DataFrame contains only expected columns
    df = df[expected_columns].replace({np.nan: None})

    # Validate DataFrame structure
    if list(df.columns) != expected_columns:
        logging.error(f"❌ Data mismatch: Expected {expected_columns}, but got {list(df.columns)}")
        return

    try:
        if category == 'registrar':
            # ✅ Insert identity first
            query_identity = """
            INSERT INTO identity (SID, lastname, firstname, NetID, grad_date)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                lastname = VALUES(lastname),
                firstname = VALUES(firstname),
                NetID = VALUES(NetID),
                grad_date = VALUES(grad_date);
            """

            identity_data = [tuple(row) for row in df[["SID", "lastname", "firstname", "NetID", "grad_date"]].values]
            cursor.executemany(query_identity, identity_data)
            conn.commit()
            logging.info(f"✅ Successfully inserted {len(identity_data)} rows into identity.")

            # ✅ Fetch valid SIDs
            cursor.execute("SELECT SID FROM identity")
            existing_sids = {row[0] for row in cursor.fetchall()}
            logging.info(f"✅ Retrieved {len(existing_sids)} valid SIDs from identity.")

            # ✅ Insert academics records (if SID exists)
            query_academics = """
            INSERT INTO academics (SID, law_gpa)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                law_gpa = VALUES(law_gpa);
            """
            
            academics_data = [tuple(row) for row in df[["SID", "law_gpa"]].values if row[0] in existing_sids]

            if not academics_data:
                logging.warning("⚠️ No valid academics records to insert after filtering SIDs!")
            else:
                cursor.executemany(query_academics, academics_data)
                conn.commit()
                logging.info(f"✅ Successfully inserted {len(academics_data)} rows into academics.")

        elif category in ['admissions', 'additional', 'bar']:
            logging.info(f"✅ Processing {category} data...")

            # Define queries for each category
            queries = {
                "admissions": """
                UPDATE academics
                SET undergrad_gpa = COALESCE(%s, undergrad_gpa),
                    lsat_score = COALESCE(%s, lsat_score)
                WHERE SID = %s;
                """,
                "additional": """
                UPDATE additional
                SET bar_review = COALESCE(%s, bar_review),
                    review_completion = COALESCE(%s, review_completion)
                WHERE SID = %s;
                """,
                "bar": """
                UPDATE bar
                SET result = COALESCE(%s, result),
                    juris = COALESCE(%s, juris)
                WHERE SID = %s;
                """
            }

            query = queries[category]

            # Update records in the database
            for _, row in df.iterrows():
                try:
                    cursor.execute(query, tuple(row[1:]) + (row["SID"],))
                except mysql.connector.Error as err:
                    logging.error(f"❌ Error updating {category} for SID {row['SID']}: {err}")

            conn.commit()
            logging.info(f"✅ Successfully updated {len(df)} {category} records.")

    except mysql.connector.Error as err:
        logging.error(f"❌ Error inserting {category}: {err}")
        conn.rollback()

        # Extra debugging: Identify problematic SIDs
        logging.info("🔍 Checking problematic SIDs...")
        if category == 'registrar':
            cursor.execute("SELECT SID FROM academics")
        else:
            cursor.execute(f"SELECT SID FROM {category}")

        valid_sids = {row[0] for row in cursor.fetchall()}
        missing_sids = [row["SID"] for _, row in df.iterrows() if row["SID"] not in valid_sids]

        if missing_sids:
            logging.warning(f"⚠️ These SIDs could not be inserted/updated: {missing_sids[:10]} (Showing 10)")

    finally:
        cursor.close()
        conn.close()

