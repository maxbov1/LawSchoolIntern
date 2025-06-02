from flask import Blueprint, render_template, request, session, redirect, jsonify, g, url_for
import json, logging
from pathlib import Path
import uuid
from dataBase.dbBuilder import build_db
from dataBase.db_helper import create_project_db
from utils.path_helper import get_project_config_dir, get_data_source_config_path

config_bp = Blueprint('config_bp', __name__)

@config_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        project_id = f"{uuid.uuid4().hex[:8]}"
        session['project_id'] = project_id

        logging.info(f"🆕 New project created in session: {project_id}")

        return redirect(url_for('config_bp.config_form'))

    return render_template('setup.html')

@config_bp.route('/config', methods=['GET'])
def config_form():
    logging.info(f"🧠 Current project ID: {session.get('project_id')}")
    project_dir = get_project_config_dir(g.project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    previous_configs = [f.name for f in project_dir.glob("*.json")]
    return render_template("config.html", previous_configs=previous_configs, data_form="config")


@config_bp.route('/save_config', methods=['POST'])
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

        config_path = get_data_source_config_path(g.project_id)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with config_path.open("w") as file:
            json.dump(config, file, indent=4)

        logging.info(f"✅ Config saved: {config_path}")
        create_project_db(g.project_id)
        build_db()
        logging.info(f"✅ Tables created in database project_{g.project_id}")

        return redirect("/home")

    except Exception as e:
        logging.error(f"❌ Error in save_config: {e}")
        return jsonify({"error": f"Failed to save configuration: {str(e)}"}), 500

