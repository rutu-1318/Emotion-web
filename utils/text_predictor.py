import joblib
import numpy as np
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# --- Safe NLTK downloads ---
def ensure_nltk_resource(resource_name, download_name=None):
    try:
        nltk.data.find(resource_name)
    except LookupError:
        nltk.download(download_name or resource_name.split('/')[-1], quiet=True)

ensure_nltk_resource('corpora/stopwords')
ensure_nltk_resource('corpora/wordnet')

# --- Load model and vectorizer ---
model = joblib.load("model/emotion_model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")
emotion_labels = model.classes_.tolist()  # safe class names

# --- Preprocessing tools ---
stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

def preprocess(text):
    """Lowercase, clean, remove stopwords, and lemmatize."""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    words = text.split()
    cleaned = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    return " ".join(cleaned)

def predict_emotion_from_text(text):
    if not text.strip():
        return "Empty input", 0.0, pd.DataFrame(columns=['Emotion', 'Probability'])

    cleaned_text = preprocess(text)

    if not cleaned_text:
        return "Unclear input", 0.0, pd.DataFrame(columns=['Emotion', 'Probability'])

    try:
        X = vectorizer.transform([cleaned_text])
        probs = model.predict_proba(X)[0]
    except Exception:
        return "Prediction Error", 0.0, pd.DataFrame(columns=['Emotion', 'Probability'])

    top_index = np.argmax(probs)
    top_emotion = emotion_labels[top_index]
    confidence = round(probs[top_index] * 100, 2)

    prob_df = pd.DataFrame({
        'Emotion': emotion_labels,
        'Probability': np.round(probs * 100, 2)
    }).set_index('Emotion')

    return top_emotion, confidence, prob_df
