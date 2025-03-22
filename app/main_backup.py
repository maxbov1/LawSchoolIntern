from flask import Flask, request, render_template,session, redirect, url_for
import os
from dataUpload.uploadCsv import allowed_file, process_csv
from datetime import datetime
import logging
import secrets
import json
import subprocess
from dataBase.dbBuilder import build_db
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

app.secret_key = secrets.token_hex(32)


@app.route('/login', methods=['POST', 'GET'])
def login():    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if username == "admin" and password == "123":
            session["user_secret_key"] = secrets.token_hex(32)
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("home"))

        return render_template("base.html", error="Invalid username or password.")

    return render_template("base.html")


@app.route('/')


@app.route('/home')
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))  # Redirect if not logged in
    return render_template("home.html")


@app.route('/upload')
def upload():
    if not session.get("logged_in"):
        return redirect(url_for("login"))  # Require login for upload
    try:
        with open('config/data_source_config.json') as f:
            config = json.load(f)
        categories = list(config['data_sources'].keys())
    except Exception as e:
        logging.error(f"Failed to load categories: {e}")
        categories = []
    return render_template('upload.html', categories=categories, message=None)


@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    # Get category selection
    category = request.form.get('category')
    if not category:
        log_message = "No category selected."
        logging.warning(log_message)
        return render_template('upload.html', message=log_message)

    # Handle file upload
    if 'file' not in request.files:
        log_message = "No file part found."
        logging.warning(log_message)
        return render_template('upload.html', message=log_message)

    file = request.files['file']
    if file.filename == '':
        log_message = "No file selected."
        logging.warning(log_message)
        return render_template('upload.html', message=log_message)

    # Validate and save the file
    if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Ensure folder exists
        file.save(filepath)

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_message = process_csv(filepath, category)
            success_message = f"{file.filename} processed and saved successfully at {timestamp}."
            logging.info(f"File uploaded: {file.filename}, Category: {category}, Status: Success")
            return render_template('upload.html', message=success_message)
        except Exception as e:
            error_message = f"Error processing file: {e}."
            logging.error(f"File uploaded: {file.filename}, Category: {category}, Status: Failed, Error: {e}")
            return render_template('upload.html', message=error_message)

    invalid_message = "Invalid file type."
    logging.warning(f"File upload failed: {file.filename}, Category: {category}, Status: Invalid file type")
    return render_template('upload.html', message=invalid_message)



TabIP = os.getenv("tableauIP")
dash_url = f"http://{TabIP}/views/YourDashboard/Sheet1"


@app.route("/dashboard")
def dashboard():
    return redirect(dash_url)

@app.route('/config', methods=['GET'])
def config_form():
    return render_template("config.html")


@app.route('/save_config', methods=['POST'])
def save_config():
    try:
        # Get all form data
        data = request.form.to_dict()

        # Extract the target variable
        target_variable = data.get("target_variable")

        # Group features and data sources
        data_sources = {}
        for key, value in data.items():
            if key.startswith("source_name_"):
                source_id = key.split("_")[2]
                source_name = value
                feature_count = int(data.get(f"feature_count_{source_id}", 0))

                # Get features for this data source
                features = []
                sensitive_columns = []
                identifier = None
                for feature_id in range(1, feature_count + 1):
                    feature_name = data.get(f"feature_name_{source_id}_{feature_id}")
                    feature_type = data.get(f"feature_type_{source_id}_{feature_id}")
                    is_sensitive = data.get(f"sensitive_{source_id}_{feature_id}") == 'on'
                    is_identifier = data.get("identifier") == f"feature_name_{source_id}_{feature_id}"

                    if is_sensitive:
                        sensitive_columns.append(feature_name)
                    if is_identifier:
                        identifier = feature_name

                    if feature_name and feature_type:
                        features.append({"name": feature_name, "type": feature_type})

                data_sources[source_name] = {
                    "features": features,
                    "sensitive_columns": sensitive_columns,
                    "identifier": identifier
                }

        # Create the final configuration dictionary
        config = {
            "target_variable": target_variable,
            "data_sources": data_sources
        }

        # Ensure the config directory exists
        os.makedirs("config", exist_ok=True)

        # Save the configuration to a JSON file
        config_path = os.path.join("config", "data_source_config.json")
        with open(config_path, "w") as file:
            json.dump(config, file, indent=4)
        return "Configuration saved successfully!"
    except Exception as e:
        return f"Error saving configuration: {str(e)}", 500


@app.route('/build_db', methods=['GET'])
def build_db_handler():
    try:
        build_db()
        return "Database created successfully!"
    except subprocess.CalledProcessError as e:
        logging.error(f"Error building db: {e.stderr}")
        return f"Error building db: {str(e)}", 500

@app.route("/logout")
def logout():
    session.clear()  # Clear session
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5050,debug=True)

