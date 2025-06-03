import mysql.connector
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import secrets
from dotenv import load_dotenv
import os

load_dotenv()


def connect_central_db():
    """ Connect to the central BarSuccess database on RDS """
    try:
        conn = mysql.connector.connect(
            host="bar-success-db-test.cluster-c0xzlo6s7duc.us-west-2.rds.amazonaws.com",
            user=os.getenv("user"),
            password=os.getenv("pwrd"),
            database="Central"
        )
        return conn
    except mysql.connector.Error as err:
        logging.error(f"❌ Central DB Connection Error: {err}")
        return None
def create_project_db(project_id):
    db_name = f"project_{project_id}_db"
    conn = connect_central_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        logging.info(f"✅ Created database: {db_name}")
    except mysql.connector.Error as err:
        logging.error(f"❌ Error creating project DB: {err}")
        raise
    finally:
        cursor.close()
        conn.close()
def connect_project_db(project_id):
    try:
        db_name = f"project_{project_id}_db"
        conn = mysql.connector.connect(
            host="bar-success-db-test.cluster-c0xzlo6s7duc.us-west-2.rds.amazonaws.com",  # ✅ updated to match Central DB host
            user=os.getenv("user"),
            password=os.getenv("pwrd"),
            database=db_name
        )
        return conn
    except mysql.connector.Error as err:
        logging.error(f"❌ Error connecting to {db_name}: {err}")
        return None


def send_invite_email(user_email, user_name, user_id, project_name):
    print("📬 Starting send_invite_email()")

    token = generate_invite_token(user_id)
    if not token:
        return False
    invite_link = f"http://localhost:5050/create_account/{token}"
    message = Mail(
        from_email='maxboving@arizona.edu',
        to_emails=user_email,
        subject=f'🎉 You’ve been invited to {project_name}!',
        html_content=f"""
<p>Hi {user_name},</p>
<p>You’ve been invited to join <strong>{project_name}</strong>. Click the button below to complete your account setup:</p>
<p>
  <a href="{invite_link}" style="
    display: inline-block;
    padding: 10px 20px;
    background-color: #1a73e8;
    color: #ffffff;
    text-decoration: none;
    border-radius: 5px;
    font-weight: bold;
  ">
    Create Your Account
  </a>
</p>
<p>If you didn’t expect this invite, you can ignore this email.</p>
"""
    )

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        logging.debug(f"📧 Invite link for {user_email}: {invite_link}")
        logging.info(f"✅ Invite email sent to {user_email} (Status: {response.status_code})")
        print(f"✅ Invite email sent to {user_email} (Status: {response.status_code})")
        print(f"📧 Invite link for {user_email}: {invite_link}")
    except Exception as e:
        logging.error(f"❌ Failed to send invite to {user_email}: {e}")

def generate_invite_token(user_id):
    token = secrets.token_urlsafe(32)
    try:
        conn = connect_central_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET invite_token=%s WHERE user_id=%s", (token, user_id))
        conn.commit()
        logging.info(f"✅ Invite token set for user {user_id}")
        return token
    except mysql.connector.Error as err:
        logging.error(f"❌ Error setting invite token: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    send_invite_email(
        user_email="maxboving@gmail.com",
        user_name="Max test",
        user_id=2,
        project_name="BarSuccess"
    )
