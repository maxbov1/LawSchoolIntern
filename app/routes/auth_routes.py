from flask import Blueprint, render_template, request, session, redirect, url_for
import secrets

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST', 'GET'])
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

@auth_bp.route('/')
@auth_bp.route('/home')
def home():
    if not session.get("logged_in"):
        return redirect(url_for("auth_bp.login"))
    return render_template("home.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth_bp.login"))
