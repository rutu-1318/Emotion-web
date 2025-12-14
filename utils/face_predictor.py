import cv2
from fer import FER
import numpy as np
import base64
from io import BytesIO
from PIL import Image

# Global FER instance (NO PyTorch)
detector = FER(mtcnn=False)

# Emotion mapping: FER → App standard
EMOTION_MAP = {
    "angry": "anger",
    "disgust": "fear",
    "fear": "fear",
    "happy": "joy",
    "sad": "sadness",
    "surprise": "surprise",
    "neutral": "neutral"
}

def map_emotion_label(fer_label):
    return EMOTION_MAP.get(fer_label, "neutral")


def predict_emotion_from_face(image):
    result = detector.detect_emotions(image)

    if result:
        emotions = result[0]["emotions"]
        mapped_emotions = {}

        for fer_label, prob in emotions.items():
            app_label = map_emotion_label(fer_label)
            mapped_emotions[app_label] = max(mapped_emotions.get(app_label, 0), prob)

        top_emotion = max(mapped_emotions, key=mapped_emotions.get)
        confidence = mapped_emotions[top_emotion]

        return top_emotion, confidence, mapped_emotions

    return "No Face Detected", 0.0, {}


def predict_emotion_from_base64(base64_image):
    try:
        if "," in base64_image:
            base64_image = base64_image.split(",")[1]

        img_bytes = base64.b64decode(base64_image)
        pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
        open_cv_image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        return predict_emotion_from_face(open_cv_image)

    except Exception as e:
        print("Error decoding image:", str(e))
        return "Error", 0.0, {}
