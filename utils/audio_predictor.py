import speech_recognition as sr
from utils.text_predictor import predict_emotion_from_text

def predict_emotion_from_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            # Transcribe audio to text
            text = recognizer.recognize_google(audio_data)
            return predict_emotion_from_text(text)
        except sr.UnknownValueError:
            return "Could not understand audio", 0.0, None
