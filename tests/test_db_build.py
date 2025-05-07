import sys
import os

# 🔧 Add app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from flask import g
from main import app  # Adjust if your app entry is named differently
from dataBase.dbBuilder import build_db
from dataBase.db_helper import create_project_db

if __name__ == "__main__":
    project_id = "c012ebd1"

    with app.app_context():
        g.project_id = project_id
        print(f"🧪 Creating project DB for project_{project_id}")
        try:
            create_project_db(project_id)  # ✅ required before build_db

            print(f"🧪 Running build_db() for project_{project_id}")
            build_db()
            print("✅ Database build successful.")
        except Exception as e:
            print(f"❌ Database build failed: {e}")

