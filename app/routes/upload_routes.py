from flask import Blueprint, render_template, request, session, redirect, current_app as app, g
import logging
from pathlib import Path

from utils.config_loader import load_config
from utils.path_helper import get_project_upload_path
from dataUpload.uploadCsv import allowed_file, process_csv

upload_bp = Blueprint('upload_bp', __name__)

@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get("logged_in"):
        return redirect("/login")

    if request.method == 'GET':
        try:
            config = load_config()
            categories = list(config.data_sources.keys())
        except Exception as e:
            logging.error(f"❌ Failed to load categories: {e}")
            categories = []
        return render_template('upload.html', categories=categories, message=None)

    # Handle POST
    category = request.form.get('category')
    if not category:
        return render_template('upload.html', message="No category selected.")

    file = request.files.get('file')
    if not file or file.filename == '':
        return render_template('upload.html', message="No file selected.")

    if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        upload_path = get_project_upload_path(g.project_id, file.filename)
        upload_path.parent.mkdir(parents=True, exist_ok=True)

        file.save(upload_path)

        try:
            result_message = process_csv(upload_path, category)
            return render_template('upload.html', message=result_message)
        except Exception as e:
            logging.error(f"❌ Error processing file: {e}")
            return render_template('upload.html', message=f"Error processing file: {e}")

    return render_template('upload.html', message="Invalid file type.")

