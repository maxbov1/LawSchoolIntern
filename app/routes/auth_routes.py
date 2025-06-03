from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import secrets
from werkzeug.security import generate_password_hash
from dataBase.db_helper import connect_central_db, send_invite_email
import mysql.connector
import os
from werkzeug.security import check_password_hash
import logging


auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = connect_central_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s", (username,))
            user = cursor.fetchone()
        except Exception as e:
            logging.error(f"❌ Login DB error: {e}")
            return "Internal server error", 500
        finally:
            cursor.close()
            conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session["user_secret_key"] = secrets.token_hex(32)
            session["logged_in"] = True
            session["username"] = user['name']
            session["user_id"] = user['user_id']
            session["project_id"] = user['project_id']
            return redirect(url_for("auth_bp.home"))

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

@auth_bp.route("/create_account/<string:token>", methods=["GET", "POST"])
def create_account(token):
    try:
        conn = connect_central_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE invite_token=%s", (token,))
        result = cursor.fetchone()
        if not result:
            flash("Invalid or expired invite token.")
            return redirect(url_for("auth_bp.login"))
        user_id = result[0]
    except mysql.connector.Error as err:
        logging.error(f"❌ DB error checking token: {err}")
        return "Internal server error", 500
    finally:
        cursor.close()
        conn.close()

    if request.method == "POST":
        password = request.form.get("password")
        if not password or len(password) < 6:
            flash("Password must be at least 6 characters.")
            return render_template("create_account.html", user_id=user_id)

        hashed_pw = generate_password_hash(password)
        try:
            conn = connect_central_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash=%s, invite_token=NULL WHERE user_id=%s", (hashed_pw, user_id))
            conn.commit()
            logging.info(f"✅ Password set for user_id {user_id}")
        except mysql.connector.Error as err:
            logging.error(f"❌ DB error setting password for user {user_id}: {err}")
            return "Internal server error", 500
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("auth_bp.login"))

    return render_template("create_account.html", user_id=user_id)

