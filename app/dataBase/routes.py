from flask import Blueprint, request, render_template, session, redirect, url_for, g
from utils.config_loader import load_config 
import mysql.connector
import os
import logging
from .encrypt import decrypt_column, decrypt_dataframe, encrypt_value
import pandas as pd
from cryptography.fernet import Fernet
from uuid import uuid4
from .db_helper import connect_central_db,connect_project_db, create_project_db



query_bp = Blueprint('query_bp', __name__, template_folder='../Templates')

def get_identifiable_fields(config):
    return sorted([config.identifier] + config.sensitive_columns)

@query_bp.route("/query", methods=["GET", "POST"])
def query_page():
    config = load_config()
    fields = get_identifiable_fields(config)  # allowed query fields (UID + sensitive)

    if request.method == "POST":
        field = request.form.get("field")
        value = request.form.get("value")

        if not field or not value:
            return render_template("query.html", fields=fields, error="Please fill in both fields.")

        try:
            conn = connect_project_db(g.project_id)

            cursor = conn.cursor(dictionary=True)

            if field == config.identifier:
                # ✅ Direct query by UID
                query = """
                    SELECT identity.*, features.*
                    FROM identity
                    JOIN features ON identity.SID = features.SID
                    WHERE identity.SID = %s
                """
                cursor.execute(query, (value,))
                results = cursor.fetchall()

            elif field in config.sensitive_columns:
                # ✅ Decrypt one column and filter
                cursor.execute("SELECT * FROM identity")
                identity_data = cursor.fetchall()
                identity_df = pd.DataFrame(identity_data)

                genkey = os.getenv("genkey")
                if not genkey:
                    raise ValueError("Missing key in environment")

                identity_df = decrypt_column(identity_df, field, genkey.encode())
                matched_sids = identity_df[identity_df[field] == value]['SID'].tolist()

                if not matched_sids:
                    results = []
                else:
                    placeholders = ', '.join(['%s'] * len(matched_sids))
                    query = f"""
                        SELECT identity.*, features.*
                        FROM identity
                        JOIN features ON identity.SID = features.SID
                        WHERE identity.SID IN ({placeholders})
                    """
                    cursor.execute(query, matched_sids)
                    results = cursor.fetchall()
                    if results:
                        df = pd.DataFrame(results)
                        df = decrypt_dataframe(df, config.sensitive_columns, genkey.encode())
                        results = df.to_dict(orient="records")

            else:
                return render_template("query.html", fields=fields, error="Invalid query field.")

            cursor.close()
            conn.close()

            return render_template("query.html", fields=fields, results=results, field=field, value=value)

        except Exception as e:
            logging.exception("Query error")
            return render_template("query.html", fields=fields, error=f"Query error: {str(e)}")

    return render_template("query.html", fields=fields)



@query_bp.route("/update_record", methods=["GET", "POST"])
def update_record():
    config = load_config()
    genkey = os.getenv("genkey")
    cipher = Fernet(genkey.encode())

    if request.method == "POST":
        sid = request.form.get("SID")
        if not sid:
            return "Missing SID", 400

        # Save changes if form has extra data beyond SID
        if len(request.form) > 1:
            try:
                updated_fields = {k: v for k, v in request.form.items() if k != "SID"}

                conn = connect_project_db(g.project_id)

                cursor = conn.cursor()


                identity_updates = []
                identity_values = []
                features_updates = []
                features_values = []

                for key, value in updated_fields.items():
                    if value in [None, '', 'None']:
                        value = None
                    if key in config.sensitive_columns:
                        identity_updates.append(f"`{key}` = %s")
                        identity_values.append(encrypt_value(value, cipher))  # ✅

                    elif key == config.identifier:
                        continue  # don't edit UID
                    else:
                        features_updates.append(f"`{key}` = %s")
                        features_values.append(value)

                if identity_updates:
                    sql = f"UPDATE identity SET {', '.join(identity_updates)} WHERE SID = %s"
                    cursor.execute(sql, identity_values + [sid])

                if features_updates:
                    sql = f"UPDATE features SET {', '.join(features_updates)} WHERE SID = %s"
                    cursor.execute(sql, features_values + [sid])

                conn.commit()
                cursor.close()
                conn.close()

            except Exception as e:
                logging.exception("Failed to save updates")
                return f"Update error: {str(e)}", 500

        # Either way, fetch latest record for display
        try:
            conn = connect_project_db(g.project_id)
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT identity.*, features.*
                FROM identity
                JOIN features ON identity.SID = features.SID
                WHERE identity.SID = %s
            """
            cursor.execute(query, (sid,))
            record = cursor.fetchone()

            cursor.close()
            conn.close()

            if not record:
                return "Record not found", 404

            df = pd.DataFrame([record])
            record = decrypt_dataframe(df, config.sensitive_columns, genkey.encode()).iloc[0].to_dict()

            return render_template("student.html", record=record, identifier=config.identifier)

        except Exception as e:
            logging.exception("Failed to load student record")
            return f"Load error: {str(e)}", 500

    else:
        return "GET method not supported for update_records", 405


@query_bp.route("/setup", methods=["GET"])
def setup_form():
    return render_template("setup.html")


@query_bp.route("/create_project", methods=["POST"])
def create_project():
    org = request.form.get("organization_name")
    proj = request.form.get("project_name")
    users = []

    for key in request.form:
        if key.startswith("users[") and key.endswith("][name]"):
            idx = key.split("[")[1].split("]")[0]
            users.append({
                "name": request.form.get(f'users[{idx}][name]'),
                "email": request.form.get(f'users[{idx}][email]'),
                "role": request.form.get(f'users[{idx}][role]')
            })

    project_id = str(uuid4())[:8]
    db_name = f"project_{project_id}"

    try:
        conn = connect_central_db()
        if conn is None:
            return "❌ Failed to connect to central DB", 500    
    
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO projects (project_id, project_name, organization_name, db_name)
            VALUES (%s, %s, %s, %s)
        """, (project_id, proj, org, db_name))

        for u in users:
            cursor.execute("""
                INSERT INTO users (name, email, role, project_id)
                VALUES (%s, %s, %s, %s)
            """, (u['name'], u['email'], u['role'], project_id))
        create_project_db(project_id)

        conn.commit()
        cursor.close()
        conn.close()

        session["project_id"] = project_id
        return redirect(url_for("config_form"))

    except Exception as e:
        return f"❌ Failed to create project: {e}", 500
