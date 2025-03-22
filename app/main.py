from flask import Flask, request, render_template, session, redirect, url_for 
import logging
import os
from datetime import datetime
import secrets
import json
import subprocess

# Importing from app subdirectories
from dataUpload.uploadCsv import allowed_file, process_csv
from dataBase.dbBuilder import build_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Flask application setup
app = Flask(
    __name__,
    template_folder="../templates",  # Corrected template path
    static_folder="../static"        # Corrected static folder path
)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.secret_key = secrets.token_hex(32)

# Tableau Dashboard IP
TabIP = os.getenv("tableauIP")
dash_url = f"http://{TabIP}/views/YourDashboard/Sheet1"

# ------------------------------
# Routes
# ------------------------------

# Login Route
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == "admin" and password == "123":
            session["user_secret_key"] = secrets.token_hex(32)
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("home"))
        
        return render_template("base.html", error="Invalid username or password.")
    return render_template("base.html")


# Home Route
@app.route('/')
@app.route('/home')
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))  # Redirect if not logged in
    return render_template("home.html")


# Upload Page
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    # Handle GET request
    if request.method == 'GET':
        try:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config/data_source_config.json')
            with open(config_path) as f:
                config = json.load(f)
            categories = list(config['data_sources'].keys())
        except Exception as e:
            logging.error(f"Failed to load categories: {e}")
            categories = []
        return render_template('upload.html', categories=categories, message=None)

    # Handle POST request (File Upload)
    category = request.form.get('category')
    if not category:
        return render_template('upload.html', message="No category selected.")

    file = request.files.get('file')
    if not file or file.filename == '':
        return render_template('upload.html', message="No file selected.")

    # Validate and save the file
    if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_message = process_csv(filepath, category)
            success_message = f"{file.filename} processed and saved successfully at {timestamp}."
            logging.info(f"✅ File uploaded: {file.filename}, Category: {category}, Status: Success")
            return render_template('upload.html', message=success_message)
        except Exception as e:
            logging.error(f"❌ Error processing file: {e}")
            return render_template('upload.html', message=f"Error processing file: {e}")

    return render_template('upload.html', message="Invalid file type.")


# Dashboard Route
@app.route("/dashboard")
def dashboard():
    return redirect(dash_url)


# Configuration Form Route
@app.route('/config', methods=['GET'])
def config_form():
    return render_template("config.html")


# Save Configuration Route
@app.route('/save_config', methods=['POST'])
def save_config():
    try:
        data = request.form.to_dict()
        data_sources = {}
        for key, value in data.items():
            if key.startswith("source_name_"):
                source_id = key.split("_")[2]
                source_name = value
                feature_count = int(data.get(f"feature_count_{source_id}", 0))
                features = []

                for feature_id in range(1, feature_count + 1):
                    feature_name = data.get(f"feature_name_{source_id}_{feature_id}")
                    feature_type = data.get(f"feature_type_{source_id}_{feature_id}")
                    if feature_name and feature_type:
                        features.append({"name": feature_name, "type": feature_type})

                data_sources[source_name] = {
                    "features": features
                }

        config = {"data_sources": data_sources}
        os.makedirs("config", exist_ok=True)
        config_path = os.path.join("config", "data_source_config.json")
        with open(config_path, "w") as file:
            json.dump(config, file, indent=4)

        logging.info(f"✅ Configuration saved successfully: {config_path}")
        return "Configuration saved successfully!"
    except Exception as e:
        logging.error(f"❌ Error saving configuration: {e}")
        return f"Error saving configuration: {str(e)}", 500


# Build Database Route
@app.route('/build_db', methods=['GET'])
def build_db_handler():
    try:
        build_db()
        return "Database created successfully!"
    except Exception as e:
        logging.error(f"❌ Error building database: {e}")
        return f"Error building database: {str(e)}", 500


# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5050)

