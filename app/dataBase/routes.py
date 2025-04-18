from flask import Blueprint, request, render_template
from utils.config_loader import load_config 
from .dataFrameToTable import db_connect
import mysql.connector
import os
import logging
from .encrypt import decrypt_column, decrypt_dataframe
import pandas as pd

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
            conn = db_connect()
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
                    raise ValueError("Missing genkey in environment")

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
