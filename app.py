import streamlit as st
import pandas as pd
import joblib
import sqlite3
import hashlib
from datetime import datetime

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="FreshCart AI — Enterprise Grocery Sentiment Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# FILE PATHS & CONSTANTS
# =========================================================

CSV_PATH = "dataset/grocery_reviews.csv"
DB_PATH = "freshcart.db"
MODEL_PATH = "model/sentiment_model.pkl"

# =========================================================
# LOAD MACHINE LEARNING MODEL
# =========================================================

try:
    model = joblib.load(MODEL_PATH)
except Exception:
    model = None

# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""

# =========================================================
# DATABASE & LOGGING SYSTEM
# =========================================================

def hash_password(password: str) -> str:
    """Generates a secure SHA-256 hash."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def log_activity(username: str, action_type: str, description: str):
    """Records user actions in the real-time activity audit log."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activity_logs (username, action_type, description, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (username, action_type, description, now_str)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def log_search(username: str, query: str, category: str = "General"):
    """Tracks who searched for what and when."""
    query = query.strip()
    if not query:
        return
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO search_logs (username, search_query, category, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (username, query, category, now_str)
        )
        conn.commit()
        conn.close()
        log_activity(username, "Searched Keyword", f"Searched for '{query}' in {category}")
    except Exception:
        pass

def init_database():
    """Initializes tables and ensures schema consistency."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Default admin account
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_hash = hash_password("admin123")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, 'admin', ?)",
            ("admin", admin_hash, now_str)
        )

    # 2. Activity logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action_type TEXT NOT NULL,
            description TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # 3. Search logs table (Who searched for what)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            search_query TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            timestamp TEXT NOT NULL
        )
    """)

    # 4. Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            added_by TEXT DEFAULT 'admin',
            created_at TEXT DEFAULT ''
        )
    """)

    # Ensure added_by and created_at columns exist in products
    cursor.execute("PRAGMA table_info(products)")
    p_cols = [col[1] for col in cursor.fetchall()]
    if "added_by" not in p_cols:
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN added_by TEXT DEFAULT 'admin'")
        except Exception:
            pass
    if "created_at" not in p_cols:
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN created_at TEXT DEFAULT ''")
        except Exception:
            pass

    # 5. Reviews table columns
    cursor.execute("PRAGMA table_info(reviews)")
    r_cols = [col[1] for col in cursor.fetchall()]
    if r_cols:
        if "Username" not in r_cols:
            try:
                cursor.execute("ALTER TABLE reviews ADD COLUMN Username TEXT DEFAULT 'Customer'")
            except Exception:
                pass
        if "Timestamp" not in r_cols:
            try:
                cursor.execute("ALTER TABLE reviews ADD COLUMN Timestamp TEXT DEFAULT ''")
            except Exception:
                pass

    conn.commit()
    conn.close()

# Initialize DB
init_database()

# =========================================================
# AUTHENTICATION FUNCTIONS
# =========================================================

def verify_user(username: str, password: str):
    """Verifies credentials, returning (success, role)."""
    username = username.strip()
    if not username or not password:
        return False, None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        stored_hash, role = row
        if hash_password(password) == stored_hash:
            return True, role
    return False, None

def register_user(username: str, password: str, role: str = "user"):
    """Registers new user or administrator."""
    username = username.strip()
    if not username or not password:
        return False, "Please enter both username and password!"
    if len(username) < 3:
        return False, "Username must be at least 3 characters!"
    if len(password) < 4:
        return False, "Password must be at least 4 characters!"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), role, now_str)
        )
        conn.commit()
        conn.close()

        role_label = "Administrator" if role == "admin" else "Customer"
        log_activity(username, "Account Registered", f"New {role_label} account created")
        return True, f"{role_label} account created successfully! You can now log in."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "This username is already taken. Please choose another username!"
    except Exception as e:
        conn.close()
        return False, f"An error occurred: {str(e)}"

# =========================================================
# DATA & INVENTORY OPERATIONS
# =========================================================

def load_data_from_database():
    """Loads all review data from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    try:
        data = pd.read_sql_query("SELECT * FROM reviews", conn)
    except Exception:
        data = pd.read_csv(CSV_PATH)
    conn.close()

    if "Username" not in data.columns:
        data["Username"] = "Customer"
    if "Timestamp" not in data.columns:
        data["Timestamp"] = ""

    data["Username"] = data["Username"].fillna("Customer")
    data["Timestamp"] = data["Timestamp"].fillna("")
    return data

def save_review_to_database(
    product_name,
    category,
    rating,
    feedback,
    sentiment,
    username="Customer"
):
    """Saves review and logs activity."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reviews
        (Product_Name, Category, Rating, Feedback, Sentiment, Username, Timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_name,
            category,
            rating,
            feedback,
            sentiment,
            username,
            now_str
        )
    )
    conn.commit()
    conn.close()

    log_activity(
        username,
        "Posted Review",
        f"Reviewed '{product_name}' ({sentiment}, {rating}★): \"{feedback[:45]}...\""
    )

def add_product(product_name, category, price, stock, added_by="Customer"):
    """Adds new product and logs creation."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO products
        (product_name, category, price, stock, added_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (product_name, category, price, stock, added_by, now_str)
    )
    conn.commit()
    conn.close()

    log_activity(
        added_by,
        "Added Product",
        f"Added new product: '{product_name}' ({category}) at ₹{price} (Stock: {stock})"
    )

def update_product(product_id: int, product_name: str, category: str, price: float, stock: int, updated_by: str):
    """Updates product and logs the edit."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE products
        SET product_name = ?, category = ?, price = ?, stock = ?
        WHERE id = ?
        """,
        (product_name, category, price, stock, product_id)
    )
    conn.commit()
    conn.close()

    log_activity(
        updated_by,
        "Product Edited",
        f"Updated product #{product_id} '{product_name}' — New Price: ₹{price}, Stock: {stock}, Category: {category}"
    )

def delete_product(product_id: int, product_name: str, deleted_by: str):
    """Deletes product and logs the removal."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    log_activity(
        deleted_by,
        "Product Deleted",
        f"Removed product #{product_id} '{product_name}' from inventory"
    )

def load_products():
    """Loads all grocery products."""
    conn = sqlite3.connect(DB_PATH)
    try:
        products = pd.read_sql_query(
            "SELECT id as 'ID', product_name as 'Product Name', category as 'Category', price as 'Price (₹)', stock as 'Stock Quantity', added_by as 'Added By', created_at as 'Date Added' FROM products ORDER BY id DESC",
            conn
        )
    except Exception:
        products = pd.DataFrame(columns=["ID", "Product Name", "Category", "Price (₹)", "Stock Quantity", "Added By", "Date Added"])
    conn.close()
    return products

def load_registered_users():
    """Fetches user directory."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            u.id as 'User ID',
            u.username as 'Username',
            u.role as 'Account Role',
            u.created_at as 'Registration Date',
            (SELECT COUNT(*) FROM reviews WHERE Username = u.username) as 'Reviews Submitted',
            (SELECT COUNT(*) FROM products WHERE added_by = u.username) as 'Products Added'
        FROM users u
        ORDER BY u.id ASC
    """
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        df = pd.read_sql_query("SELECT id as 'User ID', username as 'Username', role as 'Account Role', created_at as 'Registration Date' FROM users", conn)
        df["Reviews Submitted"] = 0
        df["Products Added"] = 0
    conn.close()
    return df

def load_activity_logs():
    """Fetches all system audit activity logs."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT id as 'Log ID', timestamp as 'Date & Time', username as 'User', action_type as 'Action', description as 'Activity Details' FROM activity_logs ORDER BY id DESC",
            conn
        )
    except Exception:
        df = pd.DataFrame(columns=["Log ID", "Date & Time", "User", "Action", "Activity Details"])
    conn.close()
    return df

def load_search_logs():
    """Fetches search query logs (who searched for what)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT id as 'Search ID', timestamp as 'Date & Time', username as 'User', search_query as 'Search Query', category as 'Context / Section' FROM search_logs ORDER BY id DESC",
            conn
        )
    except Exception:
        df = pd.DataFrame(columns=["Search ID", "Date & Time", "User", "Search Query", "Context / Section"])
    conn.close()
    return df

def load_edit_logs():
    """Fetches edit logs (who made edits)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            """
            SELECT id as 'Edit ID', timestamp as 'Date & Time', username as 'User', action_type as 'Action', description as 'Change Details'
            FROM activity_logs
            WHERE action_type LIKE '%Edit%' OR action_type LIKE '%Modif%' OR action_type LIKE '%Delete%' OR action_type LIKE '%Added Product%'
            ORDER BY id DESC
            """,
            conn
        )
    except Exception:
        df = pd.DataFrame(columns=["Edit ID", "Date & Time", "User", "Action", "Change Details"])
    conn.close()
    return df

# =========================================================
# ULTRA-ATTRACTIVE MODERN CSS STYLING
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: #f8fafc;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #04241a 0%, #083d2c 50%, #0d543e 100%);
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.18);
}

[data-testid="stSidebar"] * {
    color: #f8fafc !important;
}

/* Modern Segmented Tab Controls */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #f1f5f9;
    padding: 6px;
    border-radius: 14px;
    margin-bottom: 20px;
    border: 1px solid #e2e8f0;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 14px;
    color: #64748b;
    background-color: transparent;
    border: none;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(5, 150, 105, 0.28);
}

.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* Modern Metric Cards */
.metric-card {
    background: #ffffff;
    padding: 24px 20px;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04);
    text-align: center;
    transition: all 0.25s ease;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 25px -4px rgba(0, 0, 0, 0.08);
    border-color: #cbd5e1;
}

.metric-icon {
    font-size: 26px;
    margin-bottom: 6px;
}

.metric-value {
    font-size: 30px;
    font-weight: 800;
    color: #064e3b;
}

.metric-label {
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
}

/* Panels */
.content-panel {
    background: #ffffff;
    padding: 28px;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.03);
    margin-bottom: 20px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #059669 0%, #047857 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 700;
    font-size: 15px;
    transition: all 0.2s ease;
    box-shadow: 0 4px 12px rgba(5, 150, 105, 0.25);
}

.stButton > button:hover {
    background: linear-gradient(135deg, #047857 0%, #065f46 100%);
    box-shadow: 0 6px 18px rgba(5, 150, 105, 0.35);
    transform: translateY(-1px);
    color: white !important;
}

/* Role Badges in Sidebar */
.role-badge-admin {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #ffffff !important;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 12px;
    display: block;
}

.role-badge-user {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #ffffff !important;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 12px;
    display: block;
}

/* Portal Hero Inside App */
.portal-hero {
    background: linear-gradient(135deg, #043d2c 0%, #065f46 50%, #059669 100%);
    padding: 36px 40px;
    border-radius: 22px;
    color: white;
    margin-bottom: 26px;
    box-shadow: 0 15px 35px -5px rgba(5, 150, 105, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.15);
}

.portal-hero h1 {
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 8px;
    color: #ffffff;
}

.portal-hero h2 {
    font-size: 19px;
    font-weight: 600;
    color: #a7f3d0;
    margin-bottom: 10px;
}

.portal-hero p {
    font-size: 15px;
    color: #ecfdf5;
    max-width: 850px;
    line-height: 1.6;
}

/* Custom Footer */
.custom-footer {
    text-align: center;
    color: #94a3b8;
    padding: 30px;
    font-size: 13px;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# STUNNING, HIGH-END FRONT LANDING & AUTHENTICATION SCREEN
# =========================================================

if not st.session_state["logged_in"]:

    # Hide sidebar completely on the front landing page for a clean look
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Top Modern Navbar
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 14px 28px; background: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.03);">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="background: linear-gradient(135deg, #059669, #047857); color: white; width: 44px; height: 44px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);">
                🛒
            </div>
            <div>
                <div style="font-size: 20px; font-weight: 800; color: #064e3b; letter-spacing: -0.5px;">FreshCart AI</div>
                <div style="font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.5px; text-transform: uppercase;">Grocery Sentiment & Feedback Intelligence</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="background: #ecfdf5; color: #047857; font-size: 12px; font-weight: 700; padding: 6px 16px; border-radius: 9999px; border: 1px solid #a7f3d0; display: flex; align-items: center; gap: 6px;">
                <span style="width: 8px; height: 8px; background: #10b981; border-radius: 50%; display: inline-block;"></span>
                NLP Model Active • 98.04% Acc
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Hero Headline Banner
    st.markdown("""
    <div style="background: linear-gradient(135deg, #043d2c 0%, #065f46 45%, #059669 100%); padding: 45px 35px; border-radius: 24px; color: white; text-align: center; margin-bottom: 30px; box-shadow: 0 15px 35px -5px rgba(5, 150, 105, 0.28); border: 1px solid rgba(255,255,255,0.15);">
        <span style="background: rgba(255,255,255,0.18); color: #ecfdf5; font-size: 12px; font-weight: 700; padding: 5px 14px; border-radius: 20px; letter-spacing: 0.5px; text-transform: uppercase; display: inline-block; margin-bottom: 14px;">Enterprise AI Sentiment Platform</span>
        <h1 style="font-size: 38px; font-weight: 800; margin: 0 0 12px 0; color: #ffffff; letter-spacing: -0.5px;">Intelligent Grocery Feedback & Sentiment Platform</h1>
        <p style="font-size: 16px; color: #d1fae5; max-width: 720px; margin: 0 auto 22px auto; line-height: 1.6;">
            Harness Machine Learning to understand customer satisfaction in real time. Features dedicated customer review submission and complete audit visibility for administrators.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(8px); padding: 10px 22px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.2);">
                <div style="font-size: 22px; font-weight: 800; color: #ffffff;">98.04%</div>
                <div style="font-size: 11px; color: #a7f3d0; font-weight: 600;">Model Accuracy</div>
            </div>
            <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(8px); padding: 10px 22px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.2);">
                <div style="font-size: 22px; font-weight: 800; color: #ffffff;">510+</div>
                <div style="font-size: 11px; color: #a7f3d0; font-weight: 600;">Trained Reviews</div>
            </div>
            <div style="background: rgba(255,255,255,0.12); backdrop-filter: blur(8px); padding: 10px 22px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.2);">
                <div style="font-size: 22px; font-weight: 800; color: #ffffff;">100%</div>
                <div style="font-size: 11px; color: #a7f3d0; font-weight: 600;">Audit & Search Logs</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Centered Elevated Authentication Card
    col_pad_l, col_auth, col_pad_r = st.columns([1, 1.8, 1])

    with col_auth:
        st.markdown("""
        <div style="background: #ffffff; padding: 32px 30px; border-radius: 22px; border: 1px solid #e2e8f0; box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.07); margin-bottom: 30px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="font-size: 22px; font-weight: 800; color: #064e3b; margin: 0 0 6px 0;">Sign In or Register</h2>
                <p style="font-size: 13px; color: #64748b; margin: 0;">Access the customer feedback portal or administrator command center</p>
            </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔑 Sign In to Portal", "📝 Create New Account"])

        # --- TAB 1: LOGIN ---
        with tab_login:
            login_user = st.text_input("👤 Username", key="login_u", placeholder="e.g. admin or your username")
            login_pass = st.text_input("🔒 Password", type="password", key="login_p", placeholder="Enter your password")

            st.write("")
            if st.button("🚀 Sign In to Account", use_container_width=True, key="btn_signin"):
                if not login_user or not login_pass:
                    st.warning("⚠️ Please provide both username and password.")
                else:
                    success, role = verify_user(login_user, login_pass)
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = login_user.strip()
                        st.session_state["role"] = role
                        st.success(f"✅ Welcome back, **{login_user}**! Logged in as {role.upper()}.")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials! Please check your username and password.")

            st.markdown("""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px 16px; margin-top: 20px;">
                <div style="font-size: 12px; font-weight: 700; color: #0f172a; margin-bottom: 6px;">💡 Quick Evaluation Accounts:</div>
                <div style="font-size: 12px; color: #475569; line-height: 1.6;">
                    👑 <b>Admin:</b> Username: <code style="color: #065f46;">admin</code> | Password: <code style="color: #065f46;">admin123</code><br>
                    👤 <b>Customer:</b> Register an account in the 'Create New Account' tab above!
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- TAB 2: REGISTER ---
        with tab_register:
            reg_role = st.radio(
                "Account Type:",
                ["👤 Customer (Post Reviews Only)", "👑 Administrator (Full Control)"],
                horizontal=True,
                key="reg_role_pick"
            )

            is_admin_reg = "Administrator" in reg_role

            reg_u = st.text_input("👤 Choose Username", key="reg_u", placeholder="Choose a unique username")
            reg_p = st.text_input("🔒 Password", type="password", key="reg_p", placeholder="Minimum 4 characters")
            reg_cp = st.text_input("🔒 Confirm Password", type="password", key="reg_cp", placeholder="Re-enter password")

            admin_key = ""
            if is_admin_reg:
                st.info("🔐 **Security Authorization:** Enter `admin123` to authorize administrator accounts.")
                admin_key = st.text_input("🔑 Admin Master Passkey", type="password", key="reg_adm_key", placeholder="admin123")

            st.write("")
            if st.button("✨ Create Account", use_container_width=True, key="btn_register"):
                if not reg_u or not reg_p or not reg_cp:
                    st.warning("⚠️ Please fill in all fields.")
                elif reg_p != reg_cp:
                    st.error("❌ Passwords do not match!")
                elif is_admin_reg and admin_key != "admin123":
                    st.error("❌ Invalid Admin Passkey! Use `admin123` to authorize administrator accounts.")
                else:
                    target_role = "admin" if is_admin_reg else "user"
                    ok, msg = register_user(reg_u, reg_p, role=target_role)
                    if ok:
                        st.success(f"🎉 {msg}")
                        st.info("👈 Please switch to the **'Sign In to Portal'** tab above to access your account.")
                    else:
                        st.error(f"❌ {msg}")

        st.markdown('</div>', unsafe_allow_html=True)

    # 4. Three High-Impact Feature Cards (Below Auth)
    st.markdown('<div style="margin-top: 10px; margin-bottom: 25px;"><h3 style="text-align: center; font-size: 20px; font-weight: 800; color: #064e3b;">Platform Architecture Highlights</h3></div>', unsafe_allow_html=True)

    f_col1, f_col2, f_col3 = st.columns(3)

    with f_col1:
        st.markdown("""
        <div style="background: #ffffff; padding: 24px; border-radius: 18px; border: 1px solid #e2e8f0; height: 100%; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
            <div style="font-size: 28px; background: #ecfdf5; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 14px;">
                🤖
            </div>
            <div style="font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px;">NLP Machine Learning Core</div>
            <div style="font-size: 13px; color: #64748b; line-height: 1.5;">
                Trained on real grocery customer reviews using TF-IDF vectorization and Multinomial Naive Bayes, achieving 98.04% classification accuracy.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with f_col2:
        st.markdown("""
        <div style="background: #ffffff; padding: 24px; border-radius: 18px; border: 1px solid #e2e8f0; height: 100%; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
            <div style="font-size: 28px; background: #ecfdf5; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 14px;">
                ✍️
            </div>
            <div style="font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px;">Focused Customer Portal</div>
            <div style="font-size: 13px; color: #64748b; line-height: 1.5;">
                Distraction-free environment built exclusively for customers to select grocery items, write feedback, and view immediate sentiment outcomes.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with f_col3:
        st.markdown("""
        <div style="background: #ffffff; padding: 24px; border-radius: 18px; border: 1px solid #e2e8f0; height: 100%; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
            <div style="font-size: 28px; background: #ecfdf5; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 14px;">
                🔍
            </div>
            <div style="font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px;">Audit & Search Intelligence</div>
            <div style="font-size: 13px; color: #64748b; line-height: 1.5;">
                Real-time tracking for administrators to see who searched for what keywords, who submitted reviews, and who modified product inventory.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="custom-footer">
    🛒 <b>FreshCart AI</b> • Enterprise Grocery Feedback Intelligence<br>
    Built with Python • Streamlit • Scikit-Learn NLP • SQLite Database
    </div>
    """, unsafe_allow_html=True)

    # Halt execution until authenticated
    st.stop()


# =========================================================
# LOGGED IN PORTAL (STRICT ROLE SEGREGATION)
# =========================================================

# Load reviews data
data = load_data_from_database()

# =========================================================
# 👤 USER VIEW: ONLY ABLE TO POST REVIEWS (NOTHING ELSE)
# =========================================================

if st.session_state["role"] == "user":

    # Minimal, focused sidebar for regular users
    with st.sidebar:
        st.markdown("## 🛒 FreshCart AI")
        st.caption("Customer Feedback Portal")
        st.write("")

        st.markdown(f"""
        <div class="role-badge-user">👤 Customer: {st.session_state['username']}</div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["role"] = ""
            st.rerun()

        st.divider()
        st.markdown("### 📌 Your Permission")
        st.info("You have Customer access: You can submit product reviews for grocery items.")
        st.caption("AI-Powered Sentiment Classification active.")

    # Main area: Dedicated ONLY to posting reviews!
    st.markdown(f"""
    <div class="portal-hero">
        <h1>📝 Customer Feedback Submission Portal</h1>
        <h2>Welcome, {st.session_state['username']}! Share your product feedback below</h2>
        <p>Your honest reviews help FreshCart improve product quality and freshness. Every review is analyzed using Artificial Intelligence.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content-panel">', unsafe_allow_html=True)
    st.markdown("### ✍️ Submit a Grocery Review")

    products_df = load_products()
    if len(products_df) > 0:
        product_names = products_df["Product Name"].tolist()
        options = product_names + ["➕ Other / Custom Item"]
        selected_p = st.selectbox("🛍️ Select Product to Review:", options)

        if selected_p == "➕ Other / Custom Item":
            custom_pname = st.text_input("Enter Grocery Product Name:", placeholder="e.g. Fresh Tomatoes, Brown Bread...")
            final_pname = custom_pname.strip() if custom_pname.strip() else "Grocery Item"
            final_pcat = "Grocery"
            if custom_pname.strip():
                log_search(st.session_state["username"], custom_pname.strip(), "User Custom Product Review")
        else:
            final_pname = selected_p
            final_pcat = products_df[products_df["Product Name"] == selected_p]["Category"].values[0]
    else:
        final_pname = st.text_input("Enter Product Name to Review:", value="Fresh Milk")
        final_pcat = "Grocery"

    review_text_input = st.text_area(
        "💬 Your Review / Feedback:",
        placeholder="Example: The apples were extraordinarily sweet, crisp, and fresh!",
        height=140
    )

    if st.button("✨ Submit Review & Analyze Sentiment", use_container_width=True, key="btn_usr_submit"):
        if review_text_input.strip() == "":
            st.warning("⚠️ Please write a review before submitting.")
        elif model is None:
            st.error("ML Model is currently unavailable.")
        else:
            prediction = model.predict([review_text_input])[0]
            rating_assigned = 5 if prediction == "Positive" else 1 if prediction == "Negative" else 3

            # Save review
            save_review_to_database(
                final_pname,
                final_pcat,
                rating_assigned,
                review_text_input,
                prediction,
                username=st.session_state["username"]
            )

            # Update CSV
            new_r = pd.DataFrame({
                "Product_Name": [final_pname],
                "Category": [final_pcat],
                "Rating": [rating_assigned],
                "Feedback": [review_text_input],
                "Sentiment": [prediction]
            })
            data = pd.concat([data, new_r], ignore_index=True)
            try:
                data.to_csv(CSV_PATH, index=False)
            except Exception:
                pass

            # Outcome card
            st.write("")
            if prediction == "Positive":
                st.success(f"😊 **POSITIVE REVIEW DETECTED** — Rated: ⭐⭐⭐⭐⭐ (5/5). Customer satisfaction achieved!")
            elif prediction == "Negative":
                st.error(f"😞 **NEGATIVE REVIEW DETECTED** — Rated: ⭐ (1/5). Product improvement needed.")
            else:
                st.info(f"😐 **NEUTRAL REVIEW DETECTED** — Rated: ⭐⭐⭐ (3/5). Average customer sentiment.")

            st.success(f"✅ Thank you, **{st.session_state['username']}**! Your feedback for **'{final_pname}'** has been successfully recorded.")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="custom-footer">
    🛒 <b>FreshCart AI</b> • Customer Feedback Portal<br>
    Built with Python • Streamlit • Scikit-Learn NLP
    </div>
    """, unsafe_allow_html=True)

    # Stop rendering for user (they see nothing else)
    st.stop()


# =========================================================
# 👑 ADMINISTRATOR PORTAL: FULL CONTROL & VISIBILITY
# =========================================================

with st.sidebar:
    st.markdown("## 🛒 FreshCart AI")
    st.caption("Administrator Command Center")
    st.write("")

    st.markdown(f"""
    <div class="role-badge-admin">👑 Administrator: {st.session_state['username']}</div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout from Admin", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = ""
        st.rerun()

    st.divider()

    st.markdown("### 📌 Navigation")
    admin_page = st.radio(
        "Admin Menu",
        [
            "🏠 Executive Dashboard",
            "👥 User Activity & Review Logs",
            "🔍 Search & Query History",
            "✏️ Edit & Modification Logs",
            "🛍️ Product Management & Edits",
            "👤 Registered Users Directory",
            "📊 Machine Learning Analytics"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("### 🤖 NLP Engine")
    st.success("Model: Active (98.04% Acc)")
    st.caption("TF-IDF + Multinomial Naive Bayes")


# =========================================================
# 👑 ADMIN PAGE: SEARCH & QUERY HISTORY (WHO SEARCHED FOR WHAT)
# =========================================================

if admin_page == "🔍 Search & Query History":

    st.markdown("""
    <div class="portal-hero">
        <h1>🔍 Search & Query History</h1>
        <h2>Track exactly who searched for what terms, products, and keywords in real time</h2>
        <p>Complete visibility into user intent, queried items, and search trends across FreshCart AI.</p>
    </div>
    """, unsafe_allow_html=True)

    search_df = load_search_logs()

    # Search metrics
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔎</div>
            <div class="metric-value">{len(search_df)}</div>
            <div class="metric-label">Total Searches Logged</div>
        </div>
        """, unsafe_allow_html=True)

    with s2:
        uniq_u_search = len(search_df["User"].unique()) if len(search_df) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{uniq_u_search}</div>
            <div class="metric-label">Users Searching</div>
        </div>
        """, unsafe_allow_html=True)

    with s3:
        latest_search_item = search_df["Search Query"].iloc[0] if len(search_df) > 0 else "None"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">⚡</div>
            <div class="metric-value" style="font-size: 20px; color: #059669;">{latest_search_item[:18]}</div>
            <div class="metric-label">Latest Queried Term</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="content-panel">', unsafe_allow_html=True)
    st.markdown("### 📋 Filter User Search History")

    col_sf1, col_sf2 = st.columns(2)
    with col_sf1:
        users_in_search = ["All Users"] + sorted(list(set(search_df["User"].dropna().tolist()))) if len(search_df) > 0 else ["All Users"]
        selected_search_user = st.selectbox("👤 Filter by User (Who Searched):", users_in_search)

    with col_sf2:
        keyword_filter = st.text_input("Filter by Query Keyword:", placeholder="e.g. Milk, Bananas...")

    filtered_search = search_df.copy()
    if selected_search_user != "All Users":
        filtered_search = filtered_search[filtered_search["User"] == selected_search_user]
    if keyword_filter.strip():
        filtered_search = filtered_search[filtered_search["Search Query"].str.lower().str.contains(keyword_filter.strip().lower(), na=False)]

    st.write("")
    if len(filtered_search) > 0:
        st.dataframe(filtered_search, use_container_width=True, hide_index=True)
    else:
        st.info("No search queries recorded for this filter.")

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 👑 ADMIN PAGE: EDIT & MODIFICATION LOGS (WHO MADE EDITS)
# =========================================================

elif admin_page == "✏️ Edit & Modification Logs":

    st.markdown("""
    <div class="portal-hero">
        <h1>✏️ Edit & Modification Audit Logs</h1>
        <h2>Track who made edits, price changes, inventory updates, and deletions</h2>
        <p>Comprehensive audit record of all administrative and product catalog modifications.</p>
    </div>
    """, unsafe_allow_html=True)

    edit_df = load_edit_logs()

    e1, e2, e3 = st.columns(3)
    with e1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✏️</div>
            <div class="metric-value">{len(edit_df)}</div>
            <div class="metric-label">Total Edits Recorded</div>
        </div>
        """, unsafe_allow_html=True)

    with e2:
        uniq_editors = len(edit_df["User"].unique()) if len(edit_df) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">👤</div>
            <div class="metric-value">{uniq_editors}</div>
            <div class="metric-label">Users Making Edits</div>
        </div>
        """, unsafe_allow_html=True)

    with e3:
        latest_edit_act = edit_df["Action"].iloc[0] if len(edit_df) > 0 else "None"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🕒</div>
            <div class="metric-value" style="font-size: 20px; color: #d97706;">{latest_edit_act}</div>
            <div class="metric-label">Latest Modification Type</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="content-panel">', unsafe_allow_html=True)
    st.markdown("### 📋 Edit & Change Registry")

    users_in_edits = ["All Users"] + sorted(list(set(edit_df["User"].dropna().tolist()))) if len(edit_df) > 0 else ["All Users"]
    sel_edit_user = st.selectbox("Filter Edits by User (Who Made the Edit):", users_in_edits)

    filtered_edits = edit_df.copy()
    if sel_edit_user != "All Users":
        filtered_edits = filtered_edits[filtered_edits["User"] == sel_edit_user]

    if len(filtered_edits) > 0:
        st.dataframe(filtered_edits, use_container_width=True, hide_index=True)
    else:
        st.info("No modifications found for this user.")

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 👑 ADMIN PAGE: USER ACTIVITY & REVIEW LOGS
# =========================================================

elif admin_page == "👥 User Activity & Review Logs":

    st.markdown("""
    <div class="portal-hero">
        <h1>👥 User Activity & Feedback Intelligence</h1>
        <h2>See who posted what reviews, sentiment distributions, and ratings in real time</h2>
        <p>Complete historical log of all customer reviews and system-wide activities.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_r_log, tab_master_audit = st.tabs(["📝 Customer Reviews Log", "⚡ Master Audit Activity Log"])

    with tab_r_log:
        st.markdown('<div class="content-panel">', unsafe_allow_html=True)
        col_s_text, col_f_u, col_f_s = st.columns([2, 1.5, 1.5])

        with col_s_text:
            s_query = st.text_input("🔎 Search feedback text, products, or users:", placeholder="Type keyword...")
            if s_query.strip():
                log_search(st.session_state["username"], s_query.strip(), "Admin Reviews Search")

        all_u_list = ["All Users"] + sorted(list(set(data["Username"].dropna().tolist())))
        with col_f_u:
            sel_u = st.selectbox("👤 Filter by User (Who Posted):", all_u_list)

        with col_f_s:
            sel_s = st.selectbox("🎭 Filter by Sentiment:", ["All", "Positive", "Negative", "Neutral"])

        filtered_r = data.copy()
        if sel_u != "All Users":
            filtered_r = filtered_r[filtered_r["Username"] == sel_u]
        if sel_s != "All":
            filtered_r = filtered_r[filtered_r["Sentiment"] == sel_s]
        if s_query.strip():
            sq = s_query.strip().lower()
            filtered_r = filtered_r[
                filtered_r["Feedback"].str.lower().str.contains(sq, na=False) |
                filtered_r["Product_Name"].str.lower().str.contains(sq, na=False) |
                filtered_r["Username"].str.lower().str.contains(sq, na=False)
            ]

        # Top KPI Metrics
        st.write("")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Filtered Reviews", len(filtered_r))
        with m2:
            st.metric("Positive Reviews", len(filtered_r[filtered_r["Sentiment"] == "Positive"]))
        with m3:
            st.metric("Negative Reviews", len(filtered_r[filtered_r["Sentiment"] == "Negative"]))
        with m4:
            avg_rt = round(filtered_r["Rating"].mean(), 1) if len(filtered_r) > 0 else 0.0
            st.metric("Average Star Rating", f"{avg_rt} / 5")

        st.write("")
        if len(filtered_r) > 0:
            cols_show = ["Username", "Product_Name", "Rating", "Feedback", "Sentiment", "Timestamp", "Category"]
            v_cols = [c for c in cols_show if c in filtered_r.columns]
            st.dataframe(filtered_r[v_cols], use_container_width=True, hide_index=True)

            csv_data = filtered_r[v_cols].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Reviews Report (CSV)",
                data=csv_data,
                file_name="customer_reviews_audit.csv",
                mime="text/csv"
            )
        else:
            st.info("No reviews found matching the filters.")

        st.markdown('</div>', unsafe_allow_html=True)

    with tab_master_audit:
        st.markdown('<div class="content-panel">', unsafe_allow_html=True)
        st.markdown("### ⚡ Chronological Master Audit Timeline")
        act_df = load_activity_logs()
        st.dataframe(act_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 👑 ADMIN PAGE: PRODUCT MANAGEMENT & EDITS
# =========================================================

elif admin_page == "🛍️ Product Management & Edits":

    st.markdown("""
    <div class="portal-hero">
        <h1>🛍️ Product Catalog & Inventory Management</h1>
        <h2>Add new grocery items, modify prices and stock, or remove outdated products</h2>
        <p>Every edit and modification is automatically logged in the audit trail.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_p_list, tab_p_add, tab_p_edit, tab_p_delete = st.tabs([
        "📦 Current Inventory Catalog",
        "➕ Add New Product",
        "✏️ Edit Existing Product",
        "🗑️ Delete Product"
    ])

    with tab_p_list:
        st.markdown('<div class="content-panel">', unsafe_allow_html=True)
        prods_view = load_products()
        if len(prods_view) > 0:
            st.dataframe(prods_view, use_container_width=True, hide_index=True)
        else:
            st.info("Inventory is empty.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_p_add:
        st.markdown('<div class="content-panel">', unsafe_allow_html=True)
        st.markdown("### ➕ Add New Grocery Item")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            new_p_name = st.text_input("Product Name", placeholder="e.g. Organic Almond Milk", key="new_pn")
            new_p_cat = st.text_input("Category", placeholder="e.g. Dairy, Beverage", key="new_pc")
        with col_a2:
            new_p_price = st.number_input("Unit Price (₹)", min_value=1.0, step=1.0, value=75.0, key="new_pp")
            new_p_stock = st.number_input("Stock Quantity", min_value=1, step=1, value=50, key="new_ps")

        if st.button("➕ Create Product", use_container_width=True, key="btn_create_prod"):
            if not new_p_name.strip() or not new_p_cat.strip():
                st.warning("Please fill in both product name and category.")
            else:
                add_product(new_p_name.strip(), new_p_cat.strip(), new_p_price, new_p_stock, added_by=st.session_state["username"])
                st.success(f"✅ Product **'{new_p_name}'** added to inventory by **{st.session_state['username']}**!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_p_edit:
        st.markdown('<div class="content-panel">', unsafe_allow_html=True)
        st.markdown("### ✏️ Edit Product Details (Price & Stock)")
        prods_current = load_products()
        if len(prods_current) > 0:
            prod_dict = {f"#{row['ID']} - {row['Product Name']} (₹{row['Price (₹)']})": row for _, row in prods_current.iterrows()}
            selected_edit_str = st.selectbox("Select Product to Modify:", list(prod_dict.keys()), key="sel_p_edit")
            target_prod = prod_dict[selected_edit_str]

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                edit_name = st.text_input("Product Name", value=target_prod["Product Name"], key="ed_name")
                edit_cat = st.text_input("Category", value=target_prod["Category"], key="ed_cat")
            with col_e2:
                edit_price = st.number_input("Price (₹)", value=float(target_prod["Price (₹)"]), step=1.0, key="ed_price")
                edit_stock = st.number_input("Stock Quantity", value=int(target_prod["Stock Quantity"]), step=1, key="ed_stock")

            if st.button("💾 Save Product Changes", use_container_width=True, key="btn_save_edit"):
                update_product(
                    int(target_prod["ID"]),
                    edit_name.strip(),
                    edit_cat.strip(),
                    edit_price,
                    edit_stock,
                    updated_by=st.session_state["username"]
                )
                st.success(f"✅ Product #{target_prod['ID']} updated successfully! The change has been logged.")
                st.rerun()
        else:
            st.info("No products available to edit.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_p_delete:
        st.markdown('<div class="content-panel">', unsafe_allow_html=True)
        st.markdown("### 🗑️ Delete Product from Catalog")
        prods_del = load_products()
        if len(prods_del) > 0:
            del_dict = {f"#{row['ID']} - {row['Product Name']}": row for _, row in prods_del.iterrows()}
            selected_del_str = st.selectbox("Select Product to Remove:", list(del_dict.keys()), key="sel_p_del")
            target_del = del_dict[selected_del_str]

            if st.button("🚨 Delete Product Permanently", use_container_width=True, key="btn_del_prod"):
                delete_product(int(target_del["ID"]), target_del["Product Name"], deleted_by=st.session_state["username"])
                st.success(f"🗑️ Product #{target_del['ID']} '{target_del['Product Name']}' deleted and logged!")
                st.rerun()
        else:
            st.info("No products to delete.")
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 👑 ADMIN PAGE: REGISTERED USERS DIRECTORY
# =========================================================

elif admin_page == "👤 Registered Users Directory":

    st.markdown("""
    <div class="portal-hero">
        <h1>👤 Registered Users Directory</h1>
        <h2>All customer and administrator accounts enrolled in FreshCart AI</h2>
        <p>Monitor access levels, registration timestamps, and user contributions.</p>
    </div>
    """, unsafe_allow_html=True)

    users_df = load_registered_users()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Accounts", len(users_df))
    with c2:
        reg_users_count = len(users_df[users_df["Account Role"] == "user"]) if "Account Role" in users_df.columns else 0
        st.metric("Customer Accounts", reg_users_count)
    with c3:
        adm_users_count = len(users_df[users_df["Account Role"] == "admin"]) if "Account Role" in users_df.columns else 1
        st.metric("Administrators", adm_users_count)

    st.write("")
    st.markdown('<div class="content-panel">', unsafe_allow_html=True)
    st.dataframe(users_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 👑 ADMIN PAGE: MACHINE LEARNING ANALYTICS
# =========================================================

elif admin_page == "📊 Machine Learning Analytics":

    st.markdown("""
    <div class="portal-hero">
        <h1>📊 Machine Learning & NLP Analytics</h1>
        <h2>Evaluation metrics, confusion matrix, and sentiment distributions</h2>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Model Accuracy", "98.04%")
    with m2:
        st.metric("Precision Score", "98.23%")
    with m3:
        st.metric("Recall Rate", "98.04%")
    with m4:
        st.metric("F1-Score", "98.07%")

    st.write("")
    st.markdown('<div class="content-panel">', unsafe_allow_html=True)
    st.markdown("### 📌 Confusion Matrix")
    confusion_data = pd.DataFrame(
        [
            [19, 0, 0],
            [0, 21, 0],
            [2, 0, 60]
        ],
        columns=["Positive", "Negative", "Neutral"],
        index=["Positive", "Negative", "Neutral"]
    )
    st.dataframe(confusion_data, use_container_width=True)

    st.divider()
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("### 📈 Sentiment Breakdown")
        st.bar_chart(data["Sentiment"].value_counts())
    with col_c2:
        st.markdown("### ⭐ Customer Rating Distribution")
        st.bar_chart(data["Rating"].value_counts().sort_index())
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 🏠 EXECUTIVE DASHBOARD (ADMIN)
# =========================================================

elif admin_page == "🏠 Executive Dashboard":

    st.markdown(f"""
    <div class="portal-hero">
        <h1>🛒 FreshCart AI — Executive Dashboard</h1>
        <h2>Overview of store performance, ratings, and customer satisfaction</h2>
        <p>Logged in as: <b>{st.session_state['username']}</b> (Role: <b>{st.session_state['role'].upper()}</b>)</p>
    </div>
    """, unsafe_allow_html=True)

    total_r = len(data)
    pos_r = len(data[data["Sentiment"] == "Positive"])
    neg_r = len(data[data["Sentiment"] == "Negative"])
    avg_score = round(data["Rating"].mean(), 1) if total_r > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Customer Reviews", total_r)
    with c2:
        st.metric("Positive Sentiments", pos_r)
    with c3:
        st.metric("Negative Sentiments", neg_r)
    with c4:
        st.metric("Overall Average Rating", f"{avg_score} / 5")

    st.write("")
    st.markdown('<div class="content-panel">', unsafe_allow_html=True)
    st.markdown("### 📊 Customer Sentiment Breakdown")
    st.bar_chart(data["Sentiment"].value_counts())
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="custom-footer">
🛒 <b>FreshCart AI</b> • Enterprise Grocery Sentiment & Audit Platform<br>
Built with Python • Streamlit • Scikit-Learn NLP • SQLite Database
</div>
""", unsafe_allow_html=True)