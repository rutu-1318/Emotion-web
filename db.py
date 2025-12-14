import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASS"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT", 5432)
    )

# === USER TABLE OPERATIONS ===

def insert_user(email, phone, username, password, provider, created_at):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (email, phone, username, password, provider, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (email, phone, username, password, provider, created_at))
    conn.commit()
    cur.close()
    conn.close()


def get_user_by_email_or_phone(identifier):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM users WHERE email = %s OR phone = %s
    """, (identifier, identifier))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

# === SESSION TABLE OPERATIONS ===

def insert_session(user_id, username):
    # Skip DB session for guest users
    if username == "Guest":
        return  # do nothing

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sessions (user_id, username, is_logged_in, last_login)
        VALUES (%s, %s, TRUE, %s)
    """, (user_id, username, datetime.utcnow()))
    conn.commit()
    cur.close()
    conn.close()


# === ACTIVITY LOG OPERATIONS ===

def insert_activity(user_id, username, input_type, emotion):
    if username == "Guest":
        return  # skip logging guest activity

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO activity_log (user_id, username, input_type, emotion, timestamp)
        VALUES (%s, %s, %s, %s, NOW())
    """, (user_id, username, input_type, emotion))
    conn.commit()
    cur.close()
    conn.close()


# === OTP RESET TABLE OPERATIONS ===

def insert_otp_reset(user_id, username, otp, provider):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO otp_reset (user_id, username, otp, provider, created_at)
        VALUES (%s, %s, %s, %s, NOW())
    """, (user_id, username, otp, provider))
    conn.commit()
    cur.close()
    conn.close()


def get_training_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT text, emotion FROM emotions")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# === EMOTIONS TABLE OPERATIONS ===

def insert_emotion_if_unique(text, emotion):
    """Insert (text, emotion) into emotions table only if text is unique."""
    conn = get_db_connection()
    cur = conn.cursor()

    # check if text already exists
    cur.execute("SELECT id FROM emotions WHERE text = %s", (text,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(
            "INSERT INTO emotions (text, emotion) VALUES (%s, %s)",
            (text, emotion)
        )
        conn.commit()

    cur.close()
    conn.close()

