import sqlite3
import pandas as pd
import hashlib
from datetime import datetime

conn = sqlite3.connect("freshcart.db")
cursor = conn.cursor()

# 1. Store reviews
data = pd.read_csv("dataset/grocery_reviews.csv")
if "Username" not in data.columns:
    data["Username"] = "Customer"
if "Timestamp" not in data.columns:
    data["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

data.to_sql("reviews", conn, if_exists="replace", index=False)

# 2. Create users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")

# Default admin
cursor.execute("SELECT id FROM users WHERE username = 'admin'")
if not cursor.fetchone():
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, 'admin', ?)",
        ("admin", admin_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

# 3. Create products table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        added_by TEXT DEFAULT 'admin',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")

# 4. Create activity logs table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        action_type TEXT NOT NULL,
        description TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
""")

# 5. Create search logs table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        search_query TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        timestamp TEXT NOT NULL
    )
""")

conn.commit()

cursor.execute("SELECT COUNT(*) FROM reviews")
count = cursor.fetchone()[0]

print("Database initialized successfully!")
print("Total reviews in database:", count)

conn.close()
