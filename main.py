from flask import Flask, request, render_template
import os
from dataUpload.uploadCsv import allowed_file, process_csv
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

@app.route('/')
def upload_page():
    return render_template('upload.html', message=None)

@app.route('/upload', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True)

