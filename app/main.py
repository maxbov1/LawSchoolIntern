from flask import Flask, request, render_template, session, redirect, url_for, jsonify, Blueprint 
import logging
import os
from datetime import datetime
import secrets
import json
import subprocess
from utils.config_loader import load_config
# Importing from app subdirectories
from dataUpload.uploadCsv import allowed_file, process_csv
from dataBase.dbBuilder import build_db
from dataBase.queryFeatures import getFeatures
from machineLearning.trainModel import train_model
from machineLearning.makePredictions import makePreds
import pandas as pd
from dashboard.plot import generate_charts
from dashboard.routes import dashboard_bp
from chatbot import chatbot_bp
from dataBase.routes import query_bp
from flask import g

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Flask application setup
app = Flask(
    __name__,
    template_folder="../Templates",  # Corrected template path
    static_folder="../static"        # Corrected static folder path
)
app.register_blueprint(dashboard_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(query_bp)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.secret_key = secrets.token_hex(32)

# Tableau Dashboard IP
TabIP = os.getenv("tableauIP")
dash_url = f"http://{TabIP}/views/YourDashboard/Sheet1"

# ------------------------------
# Routes
# ------------------------------
@app.before_request
def load_project_id():
    """
    Loads the current project_id into the Flask `g` object for request-wide access.
    This must be set in the session before visiting project-specific pages.
    """
    if "project_id" not in session:
        session["project_id"] = "c012ebd1"  # Replace with your active project
        logging.warning("⚠️ Default project_id set manually for testing.")
    g.project_id = session.get("project_id")


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
    print("🧠 Current project ID:", session.get("project_id"))
    return render_template("home.html")


# Upload Page
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == 'GET':
        try:
            config = load_config()
            categories = list(config.data_sources.keys())
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

    if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"project_{g.project_id}")
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)
    
        try:
            result_message = process_csv(filepath, category)
            if 'Error' in result_message:
                return render_template('upload.html', message=result_message)
            else:
                return render_template('upload.html', message=result_message)  # Use the result_message here
        except Exception as e:
            logging.error(f"❌ Error processing file: {e}")
            return render_template('upload.html', message=f"Error processing file: {e}")

    return render_template('upload.html', message="Invalid file type.")

@app.route('/edit-permissions')
def edit_user_permissions():
    # render user permission editor here
    pass

@app.route('/config', methods=['GET'])
def config_form():
    logging.info(f"🧠 Current project ID: {session.get('project_id')}")
    config_dir = os.path.join("config", f"project_{g.project_id}")
    os.makedirs(config_dir, exist_ok=True)

    previous_configs = [
        f for f in os.listdir(config_dir) if f.endswith('.json')
    ]

    return render_template("config.html", previous_configs=previous_configs, data_form="config")

@app.route('/save_config', methods=['POST'])
def save_config():
    try:
        data = request.form.to_dict()
        data_sources = {}
        sensitive_columns = []
        identifier = None
        target_variable = data.get('target_variable')

        if not target_variable:
            logging.error("Target variable is missing!")
            return "Error: Target variable is missing.", 400

        for key, value in data.items():
            if key.startswith("source_name_"):
                source_id = key.split("_")[2]
                source_name = value
                feature_count = int(data.get(f"feature_count_{source_id}", 0))
                features = {}

                for feature_id in range(1, feature_count + 1):
                    feature_name = data.get(f"feature_name_{source_id}_{feature_id}")
                    feature_type = data.get(f"feature_type_{source_id}_{feature_id}")
                    is_sensitive = data.get(f"sensitive_{source_id}_{feature_id}") == 'on'
                    is_identifier = data.get(f"identifier_{source_id}_{feature_id}") == 'on'

                    if feature_name and feature_type:
                        features[feature_name] = feature_type
                        if is_sensitive:
                            sensitive_columns.append(feature_name)
                        if is_identifier:
                            identifier = feature_name

                data_sources[source_name] = features

        config = {
            "target_variable": target_variable,
            "identifier": identifier,
            "sensitive_columns": sensitive_columns,
            "data_sources": data_sources
        }

        project_config_dir = os.path.join("config", f"project_{g.project_id}")
        os.makedirs(project_config_dir, exist_ok=True)

        config_path = os.path.join(project_config_dir, "data_source_config.json")
        with open(config_path, "w") as file:
            json.dump(config, file, indent=4)

        logging.info(f"✅ Config saved: {config_path}")
        
        # ✅ STEP 1: Create the project DB first
        from dataBase.db_helper import create_project_db  # Add this at the top in real file
        create_project_db(g.project_id)
        logging.info(f"✅ Database created: project_{g.project_id}")

        # ✅ STEP 2: Build the project tables
        build_db()
        logging.info(f"✅ Tables created in database project_{g.project_id}")

        # ✅ Final step: Redirect or success message
        return redirect("/home")

    except Exception as e:
        logging.error(f"❌ Error in save_config: {e}")
        return jsonify({"error": f"Failed to save configuration: {str(e)}"}), 500

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


@app.route("/predictions", methods=["GET", "POST"])
def predictions():
    logging.info("🔁 /predictions endpoint hit")

    # Load config
    config_path = os.path.join("config", f"project_{g.project_id}", "data_source_config.json")
    logging.info(f"📄 Loading config from: {config_path}")
    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception as e:
        logging.error(f"❌ Failed to load config: {e}")
        return "Server error: cannot load config.", 500

    # Parse config
    try:
        target = config['target_variable']
        identifier = config['identifier']
        sensitive = set(config['sensitive_columns'])
        logging.info(f"🎯 Target: {target}, UID: {identifier}, Sensitive: {sensitive}")
    except KeyError as e:
        logging.error(f"❌ Missing key in config: {e}")
        return "Invalid config file.", 500

    # Get all valid features
    all_features = set()
    for source_name, source_fields in config['data_sources'].items():
        logging.debug(f"🧩 Processing source: {source_name} → {list(source_fields.keys())}")
        all_features.update(source_fields.keys())
    valid_features = sorted(all_features - sensitive - {identifier, target})
    logging.info(f"✅ Valid features: {valid_features}")

    # List existing models
    model_config_dir = os.path.join("config", f"project_{g.project_id}", "model_configs")
    os.makedirs(model_config_dir, exist_ok=True)
    try:
        existing_models = [
            filename.replace(".json", "")
            for filename in os.listdir(model_config_dir)
            if filename.endswith(".json")
        ]
        logging.info(f"📦 Found existing models: {existing_models}")
    except Exception as e:
        logging.error(f"❌ Failed to read model config dir: {e}")
        existing_models = []

    # Handle POST: Train model
    if request.method == "POST":
        logging.info("📝 POST request received to train model")
        model_name = request.form.get("model_name")
        selected = request.form.getlist("selected_features")
        logging.info(f"📋 Model name: {model_name}, Selected features: {selected}")

        if not selected:
            logging.warning("⚠️ No features selected for training")
            return render_template(
                "predictions.html",
                features=valid_features,
                existing_models=existing_models,
                error="Please select at least one feature."
            )

        # Save model config
        model_config = {
        'model_name': model_name,
        'features': selected,
        'target': target
        }

        model_config_dir = os.path.join("config", f"project_{g.project_id}", "model_configs")
        os.makedirs(model_config_dir, exist_ok=True)

        config_output_path = os.path.join(model_config_dir, f"{model_name}.json")
        try:
            with open(config_output_path, "w") as f:
                json.dump(model_config, f, indent=4)
            logging.info(f"💾 Saved model config: {config_output_path}")
        except Exception as e:
            logging.error(f"❌ Failed to save model config: {e}")
            return "Error saving model config.", 500

        # Train model
        try:
            df = getFeatures(columns=selected,model_name=model_name)
            train_model(df, model_name=model_name)
            logging.info(f"✅ Model '{model_name}' trained and saved.")
        except Exception as e:
            logging.error(f"❌ Model training failed: {e}")
            return f"Model training failed: {e}", 500

        return render_template(
            "predictions.html",
            features=valid_features,
            existing_models=existing_models,
            model_name=model_name,
            message=f"✅ Model '{model_name}' trained successfully!",
            data_form="predictions"
        )

    # GET: render the full prediction setup page
    return render_template(
        "predictions.html",
        features=valid_features,
        existing_models=existing_models,
        data_form="predictions"
    )


@app.route("/predict/<model_name>", methods=["GET", "POST"])
def predict_page(model_name):
    if request.method == "POST":
        file = request.files.get("predict_file")

        if not file:
            return "No file uploaded.", 400

        # Save the uploaded file temporarily
        temp_folder = os.path.join("temp", f"project_{g.project_id}")
        temp_file_path = os.path.join(temp_folder, file.filename)
        os.makedirs(temp_folder, exist_ok=True)
        file.save(temp_file_path)
        logging.info(f"file saved {file.filename } ") 

        try:
            logging.info(f" attempting predictions ")
            # Call makePreds function with model_name and path to the uploaded CSV
            predictions = makePreds(model_name, temp_file_path)
            
            logging.info(f" post predictions ")
            # Load the user data to display alongside predictions
            user_data = pd.read_csv(temp_file_path)

            # Ensure the length of predictions matches the number of rows in user_data
            if len(predictions) != len(user_data):
                return "Mismatch between number of predictions and input data.", 500

            # Add predictions to the DataFrame
            user_data["Prediction"] = predictions
            logging.info(f" predictions : {user_data.head()}")
            # Render the results in a table
            return render_template("prediction_results.html", table=user_data.to_html(classes="table table-striped"))

        except Exception as e:
            return f"An error occurred: {str(e)}", 500
    
        finally:
            # Clean up: remove the temporary file
            os.remove(temp_file_path)

    # For GET requests, render the upload form
    return render_template("predict_upload.html", model_name=model_name)


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5050)

