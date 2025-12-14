import pandas as pd
import psycopg2
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# ======================
# DATABASE CONNECTION
# ======================
conn = psycopg2.connect(
    dbname="TestDB",          # your DB name
    user="postgres",          # your user
    password="YOUR_PASSWORD", # change this
    host="localhost",
    port=5432
)

# ======================
# LOAD DATA FROM DB
# ======================
df = pd.read_sql("SELECT text, emotion FROM emotions", conn)
conn.close()

print("Rows loaded:", len(df))

X = df["text"]
y = df["emotion"]

# ======================
# TEXT VECTORIZATION
# ======================
vectorizer = TfidfVectorizer(
    max_features=5000,
    stop_words="english"
)
X_vec = vectorizer.fit_transform(X)

# ======================
# TRAIN MODEL
# ======================
model = LogisticRegression(max_iter=1000)
model.fit(X_vec, y)

# ======================
# SAVE FILES
# ======================
joblib.dump(model, "model/emotion_model.pkl")
joblib.dump(vectorizer, "model/vectorizer.pkl")

print("✅ Model and Vectorizer saved successfully")
