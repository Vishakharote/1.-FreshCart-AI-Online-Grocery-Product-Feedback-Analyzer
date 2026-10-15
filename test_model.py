import joblib

# Load the trained model
model = joblib.load("model/sentiment_model.pkl")

# Take a review from the user
review = input("Enter your grocery product review: ")

# Predict sentiment
prediction = model.predict([review])

# Display result
print("Predicted Sentiment:", prediction[0])