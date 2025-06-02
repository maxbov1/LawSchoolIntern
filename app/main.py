from flask import Flask, session, g
import logging
import secrets
import os

# Local blueprints
from routes.auth_routes import auth_bp
from routes.upload_routes import upload_bp
from routes.config_routes import config_bp
from routes.prediction_routes import prediction_bp
from dashboard.routes import dashboard_bp
from chatbot import chatbot_bp
from dataBase.routes import query_bp

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Flask app init
app = Flask(
    __name__,
    template_folder="../Templates",
    static_folder="../static"
)
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(config_bp)
app.register_blueprint(prediction_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(query_bp)

# Global context (project ID)
@app.before_request
def load_project_id():
    if "project_id" not in session:
        session["project_id"] = "c45be93f"
        logging.warning("⚠️ Default project_id set manually for testing.")
    g.project_id = session.get("project_id")

# Placeholder route
@app.route('/edit-permissions')
def edit_user_permissions():
    return "Edit user permissions page – to be implemented."

# Run app
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5050)

