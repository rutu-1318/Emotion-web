<<<<<<< HEAD
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import uuid
import subprocess
import cv2 


# Auth manager
from auth_manager import (
    send_otp_email, generate_otp, signup_user, login_user,
    send_otp_and_store, reset_password_with_otp, logout_user, send_otp_sms
)

# Project modules
from utils.text_predictor import predict_emotion_from_text
from utils.audio_predictor import predict_emotion_from_audio
from utils.face_predictor import (
    predict_emotion_from_face,
    predict_emotion_from_base64
)

# Load environment variables
load_dotenv()

# App setup
app = Flask(__name__)
app.secret_key = os.getenv("APP_KEY")

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

MAX_AUDIO_DURATION = 10  # seconds limit for uploaded/recorded audio

# -----------------------------
# Utility Decorators
# -----------------------------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('guest', False):
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

# -----------------------------
# ROUTES
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

# -----------------------------
# LOGIN / SIGNUP / OTP
# -----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        identifier = data.get('identifier', '').strip()
        password = data.get('password', '').strip()
        provider = data.get('provider', 'email')

        success, result = login_user(identifier=identifier, password=password, provider=provider)
        if success:
            session['username'] = result.get("nickname") or identifier
            return jsonify({'success': True, 'message': result.get("message")}) if request.is_json else redirect(url_for('home'))
        error_msg = result if isinstance(result, str) else result.get("message", "Login failed")
        return jsonify({'success': False, 'message': error_msg}), 401 if request.is_json else render_template('login.html', error=error_msg)
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email') or session.get('otp_email')
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        provider = request.form.get('provider', 'email')
        nickname = request.form.get('nickname', '').strip() or None

        success, msg = signup_user(username=username, nickname=nickname, password=password,
                                   email=email, phone=phone, provider=provider)
        if success:
            session['username'] = username
            return redirect(url_for('home'))
        return render_template('signup.html', error=msg)
    return render_template('signup.html')

# OTP Routes
@app.route('/send_email_otp', methods=['POST'])
def send_email_otp():
    email = request.json.get('email', '').strip()
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
    otp = generate_otp()
    session['email_otp'] = str(otp)
    session['otp_email'] = email
    try:
        send_otp_email(email, otp)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to send OTP: {str(e)}'}), 500
    return jsonify({'success': True})

@app.route('/verify_email_otp', methods=['POST'])
def verify_email_otp():
    data = request.get_json() or {}
    entered_otp = data.get('otp', '').strip()
    email = data.get('email', '').strip()
    if not email or not entered_otp:
        return jsonify({'success': False, 'error': 'Missing email or OTP'}), 400
    if email != session.get('otp_email') or entered_otp != session.get('email_otp'):
        return jsonify({'success': False, 'error': 'Invalid OTP or email mismatch'}), 401
    return jsonify({'success': True})

@app.route('/send_phone_otp', methods=['POST'])
def send_phone_otp():
    phone = request.json.get('phone', '').strip()
    if not phone:
        return jsonify({'success': False, 'error': 'Phone required'}), 400
    otp = generate_otp()
    session['phone_otp'] = str(otp)
    session['otp_phone'] = phone
    try:
        send_otp_sms(phone, otp)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to send SMS: {str(e)}'}), 500
    return jsonify({'success': True})

@app.route('/verify_phone_otp', methods=['POST'])
def verify_phone_otp():
    data = request.get_json() or {}
    entered_otp = data.get('otp', '').strip()
    phone = data.get('phone', '').strip()
    if not phone or not entered_otp:
        return jsonify({'success': False, 'error': 'Missing phone or OTP'}), 400
    if phone != session.get('otp_phone') or entered_otp != session.get('phone_otp'):
        return jsonify({'success': False, 'error': 'Invalid OTP or phone mismatch'}), 401
    return jsonify({'success': True})

@app.route('/complete_signup', methods=['POST'])
def complete_signup():
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Expected JSON'}), 400
    data = request.get_json()
    username = data.get('username', '').strip()
    nickname = data.get('nickname', '').strip() or None
    password = data.get('password', '').strip()
    provider = data.get('provider', 'email')
    email = data.get('email') or session.get('otp_email')
    phone = data.get('phone') or session.get('otp_phone')

    success, msg = signup_user(username=username, nickname=nickname, password=password,
                               email=email, phone=phone, provider=provider)
    if success:
        session['username'] = username
        return jsonify({'success': True, 'message': 'Signup successful'})
    return jsonify({'success': False, 'error': msg}), 400

# -----------------------------
# Guest Mode
# -----------------------------
@app.route('/guest')
def guest_mode():
    session.clear()
    session['guest'] = True
    session['username'] = "Guest"
    return redirect(url_for('home'))

# -----------------------------
# Home
# -----------------------------
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'], guest=session.get('guest', False))

# Demo text detection for JS async
@app.route('/demo_detect_text', methods=['POST'])
def demo_detect_text():
    if session.get('guest', False):
        return jsonify({'success': False, 'error': 'Guests cannot access text detection'}), 403
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
    try:
        top_emotion, confidence, emotion_probs = predict_emotion_from_text(text)
        return jsonify({
            'success': True,
            'emotion': top_emotion,
            'confidence': round(confidence, 2),
            'probabilities': {k: round(v * 100, 2) for k, v in emotion_probs['Probability'].items()}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Prediction error: {str(e)}'}), 500

# -----------------------------
# Detection Pages
# -----------------------------
@app.route('/text')
@login_required
def text_detector():
    return render_template('text_detector.html')

@app.route('/audio')
@login_required
def audio_detector():
    return render_template('audio_detector.html')

@app.route('/face')
@login_required
def face_detector():
    return render_template('face_detector.html')

# -----------------------------
# Detection Handlers
# -----------------------------
@app.route('/detect_text', methods=['POST'])
@login_required
def detect_text():
    text = request.form.get('text', '').strip()
    uploaded_file = request.files.get('file')
    if not text and uploaded_file and uploaded_file.filename.endswith('.txt'):
        try:
            text = uploaded_file.read().decode('utf-8').strip()
        except Exception:
            return render_template('text_detector.html', error="Failed to read uploaded file.")
    if not text:
        return render_template('text_detector.html', error="Please enter text or upload a .txt file.")
    try:
        top_emotion, confidence, emotion_probs = predict_emotion_from_text(text)
        from db import insert_emotion_if_unique
        insert_emotion_if_unique(text, top_emotion)
        labels = list(emotion_probs.index)
        probabilities = list(emotion_probs['Probability'].fillna(0).astype(float))
        return render_template('text_detector.html', emotion_result={
            'top_emotion': top_emotion,
            'confidence': round(confidence, 2),
            'labels': labels,
            'probabilities': probabilities
        })
    except Exception as e:
        return render_template('text_detector.html', error=f"Error: {str(e)}")

@app.route('/detect_audio', methods=['POST'])
@login_required
def detect_audio():
    # Get uploaded file
    file = request.files.get('audio') or request.files.get('audio_blob')
    if not file:
        return render_template('audio_detector.html', error="No audio file provided.")

    # Save file
    filename = secure_filename(file.filename) if file.filename else f"audio_{uuid.uuid4().hex}.wav"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Check duration (max 10s)
    try:
        import wave
        with wave.open(filepath, 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
            if duration > MAX_AUDIO_DURATION:
                return render_template(
                    'audio_detector.html',
                    error=f"Audio must be ≤ {MAX_AUDIO_DURATION} seconds."
                )
    except Exception:
        pass  # Ignore if duration check fails

    # Predict emotion
    try:
        top_emotion, confidence, emotion_probs = predict_emotion_from_audio(filepath)
        return render_template('audio_detector.html', emotion_result={
            'top_emotion': top_emotion,
            'confidence': round(confidence * 100, 2),
            'labels': list(emotion_probs.keys()),
            'probabilities': list(emotion_probs.values())
        })
    except Exception as e:
        return render_template('audio_detector.html', error=f"Prediction failed: {str(e)}")

@app.route('/record_audio', methods=['POST'])
@login_required
def record_audio():
    audio_file = request.files.get('audio_blob')
    if not audio_file:
        return jsonify({'error': 'No audio received'}), 400

    # Save WAV directly
    filename = f"recording_{uuid.uuid4().hex}.wav"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(filepath)

    # Optional: Check duration (if predict_emotion_from_audio can't handle >10s)
    try:
        import wave
        with wave.open(filepath, 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
            if duration > MAX_AUDIO_DURATION:
                return jsonify({'error': f"Recording must be ≤ {MAX_AUDIO_DURATION} seconds."}), 400
    except Exception:
        pass  # Ignore duration check if fails

    # Predict emotion
    try:
        top_emotion, confidence, emotion_probs = predict_emotion_from_audio(filepath)
        return jsonify({
            'success': True,
            'emotion': top_emotion,
            'confidence': round(confidence * 100, 2),
            'probabilities': {k: round(v * 100, 2) for k, v in emotion_probs.items()}
        })
    except Exception as e:
        return jsonify({'error': f"Prediction failed: {str(e)}"}), 500


@app.route('/detect_face', methods=['POST'])
@login_required
def detect_face():
    file = request.files.get('image')
    if not file:
        return render_template('face_detector.html', error="No image uploaded.")
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image = cv2.imread(filepath)
        top_emotion, confidence, emotion_probs = predict_emotion_from_face(image)
        if not emotion_probs:
            return render_template('face_detector.html', error="No face detected or failed to detect emotions.")
        labels = list(emotion_probs.keys())
        probabilities = list(emotion_probs.values())
        return render_template('face_detector.html', emotion_result={
            'top_emotion': top_emotion,
            'confidence': round(confidence*100, 2),
            'labels': labels,
            'probabilities': probabilities
        })
    except Exception as e:
        return render_template('face_detector.html', error=f"Error processing image: {str(e)}")

@app.route('/webcam_face_live', methods=['POST'])
@login_required
def webcam_face_live():
    data = request.get_json()
    base64_image = data.get('image', '')
    emotion, confidence, emotions_dict = predict_emotion_from_base64(base64_image)
    return jsonify({'success': True, 'emotion': emotion, 'confidence': round(confidence*100,2), 'probabilities': emotions_dict})

# -----------------------------
# About / Logout
# -----------------------------
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    if username and not session.get('guest', False):
        logout_user(username)
    session.clear()
    return redirect(url_for('index'))

# -----------------------------
# Error handler
# -----------------------------
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', error=str(e)), 500

# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
=======
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import uuid
import subprocess
import cv2 


# Auth manager
from auth_manager import (
    send_otp_email, generate_otp, signup_user, login_user,
    send_otp_and_store, reset_password_with_otp, logout_user, send_otp_sms
)

# Project modules
from utils.text_predictor import predict_emotion_from_text
from utils.audio_predictor import predict_emotion_from_audio
from utils.face_predictor import (
    predict_emotion_from_face,
    predict_emotion_from_base64
)

# Load environment variables
load_dotenv()

# App setup
app = Flask(__name__)
app.secret_key = os.getenv("APP_KEY")

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

MAX_AUDIO_DURATION = 10  # seconds limit for uploaded/recorded audio

# -----------------------------
# Utility Decorators
# -----------------------------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('guest', False):
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

# -----------------------------
# ROUTES
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

# -----------------------------
# LOGIN / SIGNUP / OTP
# -----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        identifier = data.get('identifier', '').strip()
        password = data.get('password', '').strip()
        provider = data.get('provider', 'email')

        success, result = login_user(identifier=identifier, password=password, provider=provider)
        if success:
            session['username'] = result.get("nickname") or identifier
            return jsonify({'success': True, 'message': result.get("message")}) if request.is_json else redirect(url_for('home'))
        error_msg = result if isinstance(result, str) else result.get("message", "Login failed")
        return jsonify({'success': False, 'message': error_msg}), 401 if request.is_json else render_template('login.html', error=error_msg)
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email') or session.get('otp_email')
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        provider = request.form.get('provider', 'email')
        nickname = request.form.get('nickname', '').strip() or None

        success, msg = signup_user(username=username, nickname=nickname, password=password,
                                   email=email, phone=phone, provider=provider)
        if success:
            session['username'] = username
            return redirect(url_for('home'))
        return render_template('signup.html', error=msg)
    return render_template('signup.html')

# OTP Routes
@app.route('/send_email_otp', methods=['POST'])
def send_email_otp():
    email = request.json.get('email', '').strip()
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
    otp = generate_otp()
    session['email_otp'] = str(otp)
    session['otp_email'] = email
    try:
        send_otp_email(email, otp)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to send OTP: {str(e)}'}), 500
    return jsonify({'success': True})

@app.route('/verify_email_otp', methods=['POST'])
def verify_email_otp():
    data = request.get_json() or {}
    entered_otp = data.get('otp', '').strip()
    email = data.get('email', '').strip()
    if not email or not entered_otp:
        return jsonify({'success': False, 'error': 'Missing email or OTP'}), 400
    if email != session.get('otp_email') or entered_otp != session.get('email_otp'):
        return jsonify({'success': False, 'error': 'Invalid OTP or email mismatch'}), 401
    return jsonify({'success': True})

@app.route('/send_phone_otp', methods=['POST'])
def send_phone_otp():
    phone = request.json.get('phone', '').strip()
    if not phone:
        return jsonify({'success': False, 'error': 'Phone required'}), 400
    otp = generate_otp()
    session['phone_otp'] = str(otp)
    session['otp_phone'] = phone
    try:
        send_otp_sms(phone, otp)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to send SMS: {str(e)}'}), 500
    return jsonify({'success': True})

@app.route('/verify_phone_otp', methods=['POST'])
def verify_phone_otp():
    data = request.get_json() or {}
    entered_otp = data.get('otp', '').strip()
    phone = data.get('phone', '').strip()
    if not phone or not entered_otp:
        return jsonify({'success': False, 'error': 'Missing phone or OTP'}), 400
    if phone != session.get('otp_phone') or entered_otp != session.get('phone_otp'):
        return jsonify({'success': False, 'error': 'Invalid OTP or phone mismatch'}), 401
    return jsonify({'success': True})

@app.route('/complete_signup', methods=['POST'])
def complete_signup():
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Expected JSON'}), 400
    data = request.get_json()
    username = data.get('username', '').strip()
    nickname = data.get('nickname', '').strip() or None
    password = data.get('password', '').strip()
    provider = data.get('provider', 'email')
    email = data.get('email') or session.get('otp_email')
    phone = data.get('phone') or session.get('otp_phone')

    success, msg = signup_user(username=username, nickname=nickname, password=password,
                               email=email, phone=phone, provider=provider)
    if success:
        session['username'] = username
        return jsonify({'success': True, 'message': 'Signup successful'})
    return jsonify({'success': False, 'error': msg}), 400

# -----------------------------
# Guest Mode
# -----------------------------
@app.route('/guest')
def guest_mode():
    session.clear()
    session['guest'] = True
    session['username'] = "Guest"
    return redirect(url_for('home'))

# -----------------------------
# Home
# -----------------------------
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'], guest=session.get('guest', False))

# Demo text detection for JS async
@app.route('/demo_detect_text', methods=['POST'])
def demo_detect_text():
    if session.get('guest', False):
        return jsonify({'success': False, 'error': 'Guests cannot access text detection'}), 403
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
    try:
        top_emotion, confidence, emotion_probs = predict_emotion_from_text(text)
        return jsonify({
            'success': True,
            'emotion': top_emotion,
            'confidence': round(confidence, 2),
            'probabilities': {k: round(v * 100, 2) for k, v in emotion_probs['Probability'].items()}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Prediction error: {str(e)}'}), 500

# -----------------------------
# Detection Pages
# -----------------------------
@app.route('/text')
@login_required
def text_detector():
    return render_template('text_detector.html')

@app.route('/audio')
@login_required
def audio_detector():
    return render_template('audio_detector.html')

@app.route('/face')
@login_required
def face_detector():
    return render_template('face_detector.html')

# -----------------------------
# Detection Handlers
# -----------------------------
@app.route('/detect_text', methods=['POST'])
@login_required
def detect_text():
    text = request.form.get('text', '').strip()
    uploaded_file = request.files.get('file')
    if not text and uploaded_file and uploaded_file.filename.endswith('.txt'):
        try:
            text = uploaded_file.read().decode('utf-8').strip()
        except Exception:
            return render_template('text_detector.html', error="Failed to read uploaded file.")
    if not text:
        return render_template('text_detector.html', error="Please enter text or upload a .txt file.")
    try:
        top_emotion, confidence, emotion_probs = predict_emotion_from_text(text)
        from db import insert_emotion_if_unique
        insert_emotion_if_unique(text, top_emotion)
        labels = list(emotion_probs.index)
        probabilities = list(emotion_probs['Probability'].fillna(0).astype(float))
        return render_template('text_detector.html', emotion_result={
            'top_emotion': top_emotion,
            'confidence': round(confidence, 2),
            'labels': labels,
            'probabilities': probabilities
        })
    except Exception as e:
        return render_template('text_detector.html', error=f"Error: {str(e)}")

@app.route('/detect_audio', methods=['POST'])
@login_required
def detect_audio():
    # Get uploaded file
    file = request.files.get('audio') or request.files.get('audio_blob')
    if not file:
        return render_template('audio_detector.html', error="No audio file provided.")

    # Save file
    filename = secure_filename(file.filename) if file.filename else f"audio_{uuid.uuid4().hex}.wav"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Check duration (max 10s)
    try:
        import wave
        with wave.open(filepath, 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
            if duration > MAX_AUDIO_DURATION:
                return render_template(
                    'audio_detector.html',
                    error=f"Audio must be ≤ {MAX_AUDIO_DURATION} seconds."
                )
    except Exception:
        pass  # Ignore if duration check fails

    # Predict emotion
    try:
        top_emotion, confidence, emotion_probs = predict_emotion_from_audio(filepath)
        return render_template('audio_detector.html', emotion_result={
            'top_emotion': top_emotion,
            'confidence': round(confidence * 100, 2),
            'labels': list(emotion_probs.keys()),
            'probabilities': list(emotion_probs.values())
        })
    except Exception as e:
        return render_template('audio_detector.html', error=f"Prediction failed: {str(e)}")

@app.route('/record_audio', methods=['POST'])
@login_required
def record_audio():
    audio_file = request.files.get('audio_blob')
    if not audio_file:
        return jsonify({'error': 'No audio received'}), 400

    # Save WAV directly
    filename = f"recording_{uuid.uuid4().hex}.wav"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(filepath)

    # Optional: Check duration (if predict_emotion_from_audio can't handle >10s)
    try:
        import wave
        with wave.open(filepath, 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
            if duration > MAX_AUDIO_DURATION:
                return jsonify({'error': f"Recording must be ≤ {MAX_AUDIO_DURATION} seconds."}), 400
    except Exception:
        pass  # Ignore duration check if fails

    # Predict emotion
    try:
        top_emotion, confidence, emotion_probs = predict_emotion_from_audio(filepath)
        return jsonify({
            'success': True,
            'emotion': top_emotion,
            'confidence': round(confidence * 100, 2),
            'probabilities': {k: round(v * 100, 2) for k, v in emotion_probs.items()}
        })
    except Exception as e:
        return jsonify({'error': f"Prediction failed: {str(e)}"}), 500


@app.route('/detect_face', methods=['POST'])
@login_required
def detect_face():
    file = request.files.get('image')
    if not file:
        return render_template('face_detector.html', error="No image uploaded.")
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image = cv2.imread(filepath)
        top_emotion, confidence, emotion_probs = predict_emotion_from_face(image)
        if not emotion_probs:
            return render_template('face_detector.html', error="No face detected or failed to detect emotions.")
        labels = list(emotion_probs.keys())
        probabilities = list(emotion_probs.values())
        return render_template('face_detector.html', emotion_result={
            'top_emotion': top_emotion,
            'confidence': round(confidence*100, 2),
            'labels': labels,
            'probabilities': probabilities
        })
    except Exception as e:
        return render_template('face_detector.html', error=f"Error processing image: {str(e)}")

@app.route('/webcam_face_live', methods=['POST'])
@login_required
def webcam_face_live():
    data = request.get_json()
    base64_image = data.get('image', '')
    emotion, confidence, emotions_dict = predict_emotion_from_base64(base64_image)
    return jsonify({'success': True, 'emotion': emotion, 'confidence': round(confidence*100,2), 'probabilities': emotions_dict})

# -----------------------------
# About / Logout
# -----------------------------
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    if username and not session.get('guest', False):
        logout_user(username)
    session.clear()
    return redirect(url_for('index'))

# -----------------------------
# Error handler
# -----------------------------
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', error=str(e)), 500

# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> c4839494da2a5a9df69db6655d4e7b1395253724
