import mysql.connector
import os
import logging

def connect_central_db():
    """ Connect to the central BarSuccess database on RDS """
    try:
        conn = mysql.connector.connect(
            host="database-barsuccess.c12a2mg6q8ex.us-west-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("pwrd"),
            database="BarSuccess"
        )
        return conn
    except mysql.connector.Error as err:
        logging.error(f"❌ Central DB Connection Error: {err}")
        return None
def create_project_db(project_id):
    db_name = f"project_{project_id}_db"
    conn = connect_central_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        logging.info(f"✅ Created database: {db_name}")
    except mysql.connector.Error as err:
        logging.error(f"❌ Error creating project DB: {err}")
        raise
    finally:
        cursor.close()
        conn.close()
def connect_project_db(project_id):
    try:
        db_name = f"project_{project_id}_db"  # ✅ match created name
        conn = mysql.connector.connect(
            host="database-barsuccess.c12a2mg6q8ex.us-west-1.rds.amazonaws.com",
            user="admin",
            password=os.getenv("pwrd"),
            database=db_name
        )
        return conn
    except mysql.connector.Error as err:
        logging.error(f"❌ Error connecting to {db_name}: {err}")
        return None
