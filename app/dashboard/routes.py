from flask import Blueprint, render_template, send_file, g
from .plot import generate_charts
import os


dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    charts_url = generate_charts()
    return render_template("dashboard.html", charts=charts_url)

@dashboard_bp.route("/chart/<int:chart_index>")
def get_chart(chart_index):
    path = f"/tmp/dashboard_charts/project_{g.project_id}/chart_{chart_index}.html"
    if os.path.exists(path):
        return send_file(path)
    return "Chart not found", 404

