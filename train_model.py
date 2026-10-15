import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib

# =========================
# Load dataset
# =========================

data = pd.read_csv("dataset/grocery_reviews.csv")

# Remove empty values
data = data.dropna(subset=["Feedback", "Sentiment"])

# =========================
# Separate input and output
# =========================

X = data["Feedback"]
y = data["Sentiment"]

# =========================
# Split dataset
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# =========================
# Create machine learning model
# =========================

model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("classifier", MultinomialNB())
])

# =========================
# Train model
# =========================

model.fit(X_train, y_train)

# =========================
# Test model
# =========================

y_pred = model.predict(X_test)

# =========================
# Calculate performance
# =========================

accuracy = accuracy_score(y_test, y_pred)

precision = precision_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

cm = confusion_matrix(y_test, y_pred)

# =========================
# Save model
# =========================

joblib.dump(model, "model/sentiment_model.pkl")

# =========================
# Display results
# =========================

print("===================================")
print("FreshCart AI - Model Performance")
print("===================================")

print(f"Accuracy  : {accuracy * 100:.2f}%")
print(f"Precision : {precision * 100:.2f}%")
print(f"Recall    : {recall * 100:.2f}%")
print(f"F1-Score  : {f1 * 100:.2f}%")

print("\nConfusion Matrix:")
print(cm)

print("\nModel trained successfully!")
print("Model saved successfully!")