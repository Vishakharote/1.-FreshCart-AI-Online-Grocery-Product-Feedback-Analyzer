import pandas as pd
import random

# Product details
products = [
    ("Amul Milk", "Dairy"),
    ("Amul Butter", "Dairy"),
    ("Amul Paneer", "Dairy"),
    ("Mother Dairy Curd", "Dairy"),
    ("Britannia Bread", "Bakery"),
    ("Brown Bread", "Bakery"),
    ("Burger Bun", "Bakery"),
    ("Chocolate Cake", "Bakery"),
    ("Fresh Apples", "Fruits"),
    ("Fresh Bananas", "Fruits"),
    ("Fresh Mangoes", "Fruits"),
    ("Fresh Oranges", "Fruits"),
    ("India Gate Rice", "Grocery"),
    ("Basmati Rice", "Grocery"),
    ("Toor Dal", "Grocery"),
    ("Tata Salt", "Grocery"),
    ("Aashirvaad Atta", "Grocery"),
    ("Lays Chips", "Snacks"),
    ("Kurkure", "Snacks"),
    ("Parle Biscuits", "Snacks")
]

# Feedback templates
positive_reviews = [
    "Very fresh and good quality",
    "Excellent product and very tasty",
    "Fresh and tasty product",
    "Very good quality product",
    "I really liked this product",
    "Product was fresh and delicious",
    "Very satisfied with the product",
    "Good quality and fresh",
    "Amazing taste and quality",
    "Highly recommended product"
]

negative_reviews = [
    "Product was stale and bad",
    "Very poor quality product",
    "Product was not fresh",
    "Taste was very bad",
    "I am not satisfied with this product",
    "Product quality was poor",
    "Very disappointing product",
    "Product was damaged",
    "Not fresh and not tasty",
    "I would not recommend this product"
]

neutral_reviews = [
    "Product quality was average",
    "Taste was okay",
    "The product was normal",
    "Average quality product",
    "It was neither good nor bad",
    "Product was acceptable",
    "Taste was average",
    "Quality was okay",
    "The product was satisfactory",
    "Nothing special about this product"
]

data = []

# Create 500 reviews
for i in range(500):

    product, category = random.choice(products)

    # Create balanced sentiment data
    choice = random.randint(1, 10)

    if choice <= 6:
        sentiment = "Positive"
        feedback = random.choice(positive_reviews)
        rating = random.randint(4, 5)

    elif choice <= 8:
        sentiment = "Negative"
        feedback = random.choice(negative_reviews)
        rating = random.randint(1, 2)

    else:
        sentiment = "Neutral"
        feedback = random.choice(neutral_reviews)
        rating = 3

    data.append([
        product,
        category,
        rating,
        feedback,
        sentiment
    ])

# Create DataFrame
df = pd.DataFrame(
    data,
    columns=[
        "Product_Name",
        "Category",
        "Rating",
        "Feedback",
        "Sentiment"
    ]
)

# Save dataset
df.to_csv(
    "dataset/grocery_reviews.csv",
    index=False
)

print("500 records created successfully!")
print("Dataset saved in dataset/grocery_reviews.csv")

print("\nSentiment Count:")
print(df["Sentiment"].value_counts())

print("\nCategory Count:")
print(df["Category"].value_counts())