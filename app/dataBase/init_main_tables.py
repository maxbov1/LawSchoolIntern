import mysql.connector
import os
import logging
from .db_helper import connect_central_db

def create_projects_and_users_tables():
    logging.info("🔨 Creating `projects` and `users` tables in main DB...")

    create_projects = """
        CREATE TABLE IF NOT EXISTS projects (
            project_id VARCHAR(50) PRIMARY KEY,
            project_name VARCHAR(100) NOT NULL,
            organization_name VARCHAR(100) NOT NULL,
            db_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    create_users = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            role ENUM('uploader', 'viewer', 'analyst') NOT NULL,
            project_id VARCHAR(50),
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
        );
    """

    try:
        conn = connect_central_db()
        cursor = conn.cursor()
        cursor.execute(create_projects)
        cursor.execute(create_users)
        conn.commit()
        logging.info("✅ `projects` and `users` tables created successfully.")
    except Exception as e:
        logging.error(f"❌ Failed to create tables: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_projects_and_users_tables()

