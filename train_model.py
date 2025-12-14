<<<<<<< HEAD
import psycopg2
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("PG_DB"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASS"),
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT", 5432)
)

cur = conn.cursor()
cur.execute("SELECT text, emotion FROM emotions")
rows = cur.fetchall()

if not rows:
    print("❌ emotions table is empty")
    exit()

texts, labels = zip(*rows)

print(f"✅ Rows loaded: {len(texts)}")

vectorizer = TfidfVectorizer(max_features=5000)
X = vectorizer.fit_transform(texts)

model = LogisticRegression(max_iter=1000)
model.fit(X, labels)

os.makedirs("model", exist_ok=True)

joblib.dump(model, "model/emotion_model.pkl")
joblib.dump(vectorizer, "model/vectorizer.pkl")

print("✅ Model and vectorizer saved")

cur.close()
conn.close()
=======
import psycopg2
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("PG_DB"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASS"),
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT", 5432)
)

cur = conn.cursor()
cur.execute("SELECT text, emotion FROM emotions")
rows = cur.fetchall()

if not rows:
    print("❌ emotions table is empty")
    exit()

texts, labels = zip(*rows)

print(f"✅ Rows loaded: {len(texts)}")

vectorizer = TfidfVectorizer(max_features=5000)
X = vectorizer.fit_transform(texts)

model = LogisticRegression(max_iter=1000)
model.fit(X, labels)

os.makedirs("model", exist_ok=True)

joblib.dump(model, "model/emotion_model.pkl")
joblib.dump(vectorizer, "model/vectorizer.pkl")

print("✅ Model and vectorizer saved")

cur.close()
conn.close()
>>>>>>> c4839494da2a5a9df69db6655d4e7b1395253724
