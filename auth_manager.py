<<<<<<< HEAD
# auth_manager.py (profile_pic removed)
import bcrypt
import random
import smtplib
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from db import get_db_connection

load_dotenv()

ALLOWED_PROVIDERS = {"email", "phone", "google"}

# === Password Utilities ===
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# === OTP Utilities ===
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    """Send OTP via SMTP. Requires EMAIL_USER & EMAIL_PASS in env."""
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    if not sender_email or not sender_password:
        raise Exception("Email credentials not set")

    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "OTP Verification"
    msg["From"] = sender_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)

def send_otp_sms(to_phone, otp):
    """
    Placeholder SMS sender for development.
    Replace this with Twilio or another SMS provider for production.
    """
    print(f"[DEBUG] OTP for {to_phone}: {otp}")
    return True

# === SIGNUP ===
def signup_user(username, nickname=None, password=None, email=None, phone=None, provider=None):
    """
    Create a new user. profile_pic support removed.
    Returns (success: bool, message_or_payload)
    """
    if provider not in ALLOWED_PROVIDERS:
        return False, f"Unsupported provider: {provider}"

    if not username:
        return False, "Username is required"

    if provider in {"email", "phone"}:
        if not password:
            return False, "Password is required"
        if provider == "email" and not email:
            return False, "Email is required for email signup"
        if provider == "phone" and not phone:
            return False, "Phone number is required for phone signup"

    if provider == 'google' and not email:
        return False, "Email is required for Google signup"

    conn = get_db_connection()
    cur = conn.cursor()

    # Check for duplicates
    cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False, "Username already exists"

    if email:
        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, "Email already registered"

    if phone:
        cur.execute("SELECT 1 FROM users WHERE phone = %s", (phone,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, "Phone number already registered"

    hashed_pw = hash_password(password) if password else None

    cur.execute("""
        INSERT INTO users (username, nickname, password, email, phone, provider, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING user_id
    """, (username, nickname, hashed_pw, email, phone, provider, datetime.now()))

    user_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO sessions (user_id, is_logged_in, last_login)
        VALUES (%s, TRUE, %s)
    """, (user_id, datetime.now()))

    conn.commit()
    cur.close()
    conn.close()
    return True, "Signup successful"

# === LOGIN ===
def login_user(identifier, password=None, provider=None):
    if provider not in ALLOWED_PROVIDERS:
        return False, f"Unsupported provider: {provider}"

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, password, provider, nickname
        FROM users 
        WHERE email = %s OR phone = %s OR username = %s
    """, (identifier, identifier, identifier))

    result = cur.fetchone()
    if not result:
        cur.close()
        conn.close()
        return False, "User not found"

    user_id, hashed_pw, registered_provider, nickname = result

    if provider != registered_provider:
        cur.close()
        conn.close()
        return False, f"Account is registered via {registered_provider}"

    if provider in {"email", "phone"} and (not hashed_pw or not verify_password(password, hashed_pw)):
        cur.close()
        conn.close()
        return False, "Invalid password"

    # Update session
    cur.execute("SELECT 1 FROM sessions WHERE user_id = %s", (user_id,))
    if cur.fetchone():
        cur.execute("UPDATE sessions SET is_logged_in = TRUE, last_login = %s WHERE user_id = %s",
                    (datetime.now(), user_id))
    else:
        cur.execute("INSERT INTO sessions (user_id, is_logged_in, last_login) VALUES (%s, TRUE, %s)",
                    (user_id, datetime.now()))

    conn.commit()
    cur.close()
    conn.close()
    return True, {"message": "Login successful", "nickname": nickname}

# === LOGOUT ===
def logout_user(username):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return False, "User not found"

    user_id = user[0]
    cur.execute("UPDATE sessions SET is_logged_in = FALSE WHERE user_id = %s", (user_id,))

    conn.commit()
    cur.close()
    conn.close()
    return True, "Logout successful"

# === OTP for password-reset (unchanged) ===
def send_otp_and_store(username):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id, email FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return False, "User not found"

    user_id, email = user
    if not email:
        cur.close()
        conn.close()
        return False, "No email associated with this account"

    otp = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=10)

    try:
        send_otp_email(email, otp)
    except Exception as e:
        cur.close()
        conn.close()
        return False, f"Failed to send OTP: {str(e)}"

    cur.execute("INSERT INTO otp_reset (user_id, otp, expires_at) VALUES (%s, %s, %s)",
                (user_id, otp, expires_at))
    conn.commit()
    cur.close()
    conn.close()
    return True, "OTP sent"

def reset_password_with_otp(username, otp, new_password):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return False, "User not found"

    user_id = user[0]
    cur.execute("SELECT otp, expires_at FROM otp_reset WHERE user_id = %s ORDER BY expires_at DESC LIMIT 1",
                (user_id,))
    otp_data = cur.fetchone()
    if not otp_data:
        cur.close()
        conn.close()
        return False, "OTP not found"

    db_otp, expires_at = otp_data
    if datetime.now() > expires_at:
        cur.close()
        conn.close()
        return False, "OTP expired"

    if otp != db_otp:
        cur.close()
        conn.close()
        return False, "Invalid OTP"

    hashed_pw = hash_password(new_password)
    cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_pw, user_id))
    conn.commit()

    cur.close()
    conn.close()
    return True, "Password reset successful"
=======
# auth_manager.py (profile_pic removed)
import bcrypt
import random
import smtplib
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from db import get_db_connection

load_dotenv()

ALLOWED_PROVIDERS = {"email", "phone", "google"}

# === Password Utilities ===
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# === OTP Utilities ===
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    """Send OTP via SMTP. Requires EMAIL_USER & EMAIL_PASS in env."""
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    if not sender_email or not sender_password:
        raise Exception("Email credentials not set")

    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "OTP Verification"
    msg["From"] = sender_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)

def send_otp_sms(to_phone, otp):
    """
    Placeholder SMS sender for development.
    Replace this with Twilio or another SMS provider for production.
    """
    print(f"[DEBUG] OTP for {to_phone}: {otp}")
    return True

# === SIGNUP ===
def signup_user(username, nickname=None, password=None, email=None, phone=None, provider=None):
    """
    Create a new user. profile_pic support removed.
    Returns (success: bool, message_or_payload)
    """
    if provider not in ALLOWED_PROVIDERS:
        return False, f"Unsupported provider: {provider}"

    if not username:
        return False, "Username is required"

    if provider in {"email", "phone"}:
        if not password:
            return False, "Password is required"
        if provider == "email" and not email:
            return False, "Email is required for email signup"
        if provider == "phone" and not phone:
            return False, "Phone number is required for phone signup"

    if provider == 'google' and not email:
        return False, "Email is required for Google signup"

    conn = get_db_connection()
    cur = conn.cursor()

    # Check for duplicates
    cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False, "Username already exists"

    if email:
        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, "Email already registered"

    if phone:
        cur.execute("SELECT 1 FROM users WHERE phone = %s", (phone,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, "Phone number already registered"

    hashed_pw = hash_password(password) if password else None

    cur.execute("""
        INSERT INTO users (username, nickname, password, email, phone, provider, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING user_id
    """, (username, nickname, hashed_pw, email, phone, provider, datetime.now()))

    user_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO sessions (user_id, is_logged_in, last_login)
        VALUES (%s, TRUE, %s)
    """, (user_id, datetime.now()))

    conn.commit()
    cur.close()
    conn.close()
    return True, "Signup successful"

# === LOGIN ===
def login_user(identifier, password=None, provider=None):
    if provider not in ALLOWED_PROVIDERS:
        return False, f"Unsupported provider: {provider}"

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, password, provider, nickname
        FROM users 
        WHERE email = %s OR phone = %s OR username = %s
    """, (identifier, identifier, identifier))

    result = cur.fetchone()
    if not result:
        cur.close()
        conn.close()
        return False, "User not found"

    user_id, hashed_pw, registered_provider, nickname = result

    if provider != registered_provider:
        cur.close()
        conn.close()
        return False, f"Account is registered via {registered_provider}"

    if provider in {"email", "phone"} and (not hashed_pw or not verify_password(password, hashed_pw)):
        cur.close()
        conn.close()
        return False, "Invalid password"

    # Update session
    cur.execute("SELECT 1 FROM sessions WHERE user_id = %s", (user_id,))
    if cur.fetchone():
        cur.execute("UPDATE sessions SET is_logged_in = TRUE, last_login = %s WHERE user_id = %s",
                    (datetime.now(), user_id))
    else:
        cur.execute("INSERT INTO sessions (user_id, is_logged_in, last_login) VALUES (%s, TRUE, %s)",
                    (user_id, datetime.now()))

    conn.commit()
    cur.close()
    conn.close()
    return True, {"message": "Login successful", "nickname": nickname}

# === LOGOUT ===
def logout_user(username):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return False, "User not found"

    user_id = user[0]
    cur.execute("UPDATE sessions SET is_logged_in = FALSE WHERE user_id = %s", (user_id,))

    conn.commit()
    cur.close()
    conn.close()
    return True, "Logout successful"

# === OTP for password-reset (unchanged) ===
def send_otp_and_store(username):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id, email FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return False, "User not found"

    user_id, email = user
    if not email:
        cur.close()
        conn.close()
        return False, "No email associated with this account"

    otp = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=10)

    try:
        send_otp_email(email, otp)
    except Exception as e:
        cur.close()
        conn.close()
        return False, f"Failed to send OTP: {str(e)}"

    cur.execute("INSERT INTO otp_reset (user_id, otp, expires_at) VALUES (%s, %s, %s)",
                (user_id, otp, expires_at))
    conn.commit()
    cur.close()
    conn.close()
    return True, "OTP sent"

def reset_password_with_otp(username, otp, new_password):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return False, "User not found"

    user_id = user[0]
    cur.execute("SELECT otp, expires_at FROM otp_reset WHERE user_id = %s ORDER BY expires_at DESC LIMIT 1",
                (user_id,))
    otp_data = cur.fetchone()
    if not otp_data:
        cur.close()
        conn.close()
        return False, "OTP not found"

    db_otp, expires_at = otp_data
    if datetime.now() > expires_at:
        cur.close()
        conn.close()
        return False, "OTP expired"

    if otp != db_otp:
        cur.close()
        conn.close()
        return False, "Invalid OTP"

    hashed_pw = hash_password(new_password)
    cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_pw, user_id))
    conn.commit()

    cur.close()
    conn.close()
    return True, "Password reset successful"
>>>>>>> c4839494da2a5a9df69db6655d4e7b1395253724
