import streamlit as st
import pandas as pd
import joblib
import sqlite3

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="FreshCart AI",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# FILE PATHS
# =========================

CSV_PATH = "dataset/grocery_reviews.csv"
DB_PATH = "freshcart.db"
MODEL_PATH = "model/sentiment_model.pkl"

# =========================
# LOAD MODEL
# =========================

model = joblib.load(MODEL_PATH)

# =========================
# DATABASE FUNCTIONS
# =========================

def load_data_from_database():

    conn = sqlite3.connect(DB_PATH)

    try:
        data = pd.read_sql_query(
            "SELECT * FROM reviews",
            conn
        )
    except Exception:
        data = pd.read_csv(CSV_PATH)

    conn.close()

    return data


def save_review_to_database(
    product_name,
    category,
    rating,
    feedback,
    sentiment
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reviews
        (Product_Name, Category, Rating, Feedback, Sentiment)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            product_name,
            category,
            rating,
            feedback,
            sentiment
        )
    )

    conn.commit()
    conn.close()


# =========================
# PRODUCT DATABASE
# =========================

def create_products_table():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def add_product(
    product_name,
    category,
    price,
    stock
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products
        (product_name, category, price, stock)
        VALUES (?, ?, ?, ?)
        """,
        (
            product_name,
            category,
            price,
            stock
        )
    )

    conn.commit()
    conn.close()


def load_products():

    conn = sqlite3.connect(DB_PATH)

    products = pd.read_sql_query(
        "SELECT * FROM products",
        conn
    )

    conn.close()

    return products


# Create products table
create_products_table()


# =========================
# LOAD DATA
# =========================

data = load_data_from_database()


# =========================
# CSS
# =========================

st.markdown("""
<style>

.stApp {
    background: #f5f8f4;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #12372a, #1f5c43);
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.hero {
    background: linear-gradient(135deg, #12372a, #2d7d57);
    padding: 45px;
    border-radius: 25px;
    color: white;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.12);
}

.hero h1 {
    font-size: 45px;
    margin-bottom: 10px;
}

.hero p {
    font-size: 19px;
    color: #e7f5eb;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 20px;
    text-align: center;
    box-shadow: 0 5px 20px rgba(0,0,0,0.07);
    border: 1px solid #e6eee8;
}

.card-number {
    font-size: 32px;
    font-weight: bold;
    color: #17633f;
}

.card-title {
    color: #68756d;
    font-size: 15px;
}

.section-title {
    font-size: 27px;
    font-weight: bold;
    color: #173b2b;
    margin-top: 25px;
}

.review-box {
    background: white;
    padding: 30px;
    border-radius: 22px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.07);
}

.stButton > button {
    background: linear-gradient(90deg, #17633f, #2d8a5d);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 25px;
    font-weight: bold;
}

.stButton > button:hover {
    background: #12372a;
    color: white;
}

textarea {
    border-radius: 15px !important;
}

.footer {
    text-align: center;
    color: #718078;
    padding: 25px;
    font-size: 14px;
}

</style>
""", unsafe_allow_html=True)


# =========================
# SIDEBAR NAVIGATION
# =========================

with st.sidebar:

    st.markdown("## 🛒 FreshCart AI")

    st.write("")

    st.markdown("### 📌 Navigation")

    page = st.radio(
        "Go to",
        [
            "🏠 Dashboard",
            "🔍 Review Analyzer",
            "📊 Analytics",
            "🛍️ Products"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("### 🤖 AI Model")

    st.success("Model: Active")

    st.write("Algorithm:")
    st.write("TF-IDF + Multinomial Naive Bayes")

    st.divider()

    st.caption("Online Grocery Product Feedback Analyzer")


# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":

    st.markdown("""
    <div class="hero">

    <h1>🛒 FreshCart AI</h1>

    <h2>Online Grocery Product Feedback Analyzer</h2>

    <p>
    Understand your customers better using
    Artificial Intelligence & Machine Learning.
    </p>

    </div>
    """, unsafe_allow_html=True)

    total = len(data)

    positive = len(
        data[data["Sentiment"] == "Positive"]
    )

    negative = len(
        data[data["Sentiment"] == "Negative"]
    )

    neutral = len(
        data[data["Sentiment"] == "Neutral"]
    )

    avg_rating = round(
        data["Rating"].mean(),
        1
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(f"""
        <div class="card">
            <div class="card-number">📋 {total}</div>
            <div class="card-title">Total Reviews</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:

        st.markdown(f"""
        <div class="card">
            <div class="card-number">😊 {positive}</div>
            <div class="card-title">Positive Reviews</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:

        st.markdown(f"""
        <div class="card">
            <div class="card-number">😞 {negative}</div>
            <div class="card-title">Negative Reviews</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:

        st.markdown(f"""
        <div class="card">
            <div class="card-number">⭐ {avg_rating}</div>
            <div class="card-title">Average Rating</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # =========================
    # REVIEW ANALYZER
    # =========================

    st.markdown(
        '<div class="section-title">🔍 AI Review Analyzer</div>',
        unsafe_allow_html=True
    )

    st.write("")

    st.markdown("""
    <div class="review-box">
    <b>Enter customer feedback below.</b><br>
    Our Machine Learning model will identify whether the review is
    Positive, Negative or Neutral.
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    review = st.text_area(
        "Customer Review",
        placeholder="Example: The apples were fresh, sweet and tasty...",
        height=130
    )

    if st.button(
        "✨ Analyze Customer Feedback",
        use_container_width=True
    ):

        if review.strip() == "":

            st.warning(
                "Please enter a customer review."
            )

        else:

            prediction = model.predict(
                [review]
            )[0]

            rating = (
                5 if prediction == "Positive"
                else 1 if prediction == "Negative"
                else 3
            )

            # SAVE TO DATABASE

            save_review_to_database(
                "Customer Review",
                "Grocery",
                rating,
                review,
                prediction
            )

            # SAVE TO CSV

            new_row = pd.DataFrame({

                "Product_Name": [
                    "Customer Review"
                ],

                "Category": [
                    "Grocery"
                ],

                "Rating": [
                    rating
                ],

                "Feedback": [
                    review
                ],

                "Sentiment": [
                    prediction
                ]
            })

            data = pd.concat(
                [data, new_row],
                ignore_index=True
            )

            data.to_csv(
                CSV_PATH,
                index=False
            )

            # SHOW RESULT

            if prediction == "Positive":

                st.success(
                    "😊 POSITIVE REVIEW — Customer is satisfied!"
                )

            elif prediction == "Negative":

                st.error(
                    "😞 NEGATIVE REVIEW — Customer may not be satisfied."
                )

            else:

                st.info(
                    "😐 NEUTRAL REVIEW — Customer feedback is average."
                )

            st.write("")

            st.markdown(
                '<div class="section-title">📊 Updated Customer Sentiment Graph</div>',
                unsafe_allow_html=True
            )

            sentiment_count = (
                data["Sentiment"]
                .value_counts()
            )

            st.bar_chart(
                sentiment_count
            )

            st.success(
                "✅ New review saved successfully in database and CSV!"
            )

            st.info(
                "📁 Database: freshcart.db"
            )

    else:

        st.write("")

        st.markdown(
            '<div class="section-title">📊 Customer Sentiment Graph</div>',
            unsafe_allow_html=True
        )

        sentiment_count = (
            data["Sentiment"]
            .value_counts()
        )

        st.bar_chart(
            sentiment_count
        )


# =========================================================
# REVIEW ANALYZER PAGE
# =========================================================

elif page == "🔍 Review Analyzer":

    st.markdown(
        '<div class="section-title">🔍 AI Review Analyzer</div>',
        unsafe_allow_html=True
    )

    st.write("")

    # =========================
    # SELECT PRODUCT
    # =========================

    products = load_products()

    if len(products) > 0:

        product_list = products["product_name"].tolist()

        selected_product = st.selectbox(
            "🛍️ Select Product",
            product_list
        )

    else:

        selected_product = "Customer Review"

        st.info(
            "Please add products from the Products section first."
        )

    st.write("")

    # =========================
    # ENTER REVIEW
    # =========================

    review = st.text_area(
        "Enter Customer Review",
        placeholder="Example: Apple is good and fresh...",
        height=150
    )

    if st.button(
        "✨ Analyze Customer Feedback",
        use_container_width=True
    ):

        if review.strip() == "":

            st.warning(
                "Please enter a review."
            )

        else:

            prediction = model.predict(
                [review]
            )[0]

            rating = (
                5 if prediction == "Positive"
                else 1 if prediction == "Negative"
                else 3
            )

            # SAVE TO DATABASE

            save_review_to_database(
                selected_product,
                "Grocery",
                rating,
                review,
                prediction
            )

            # SAVE TO CSV

            new_row = pd.DataFrame({

                "Product_Name": [
                    selected_product
                ],

                "Category": [
                    "Grocery"
                ],

                "Rating": [
                    rating
                ],

                "Feedback": [
                    review
                ],

                "Sentiment": [
                    prediction
                ]
            })

            data = pd.concat(
                [data, new_row],
                ignore_index=True
            )

            data.to_csv(
                CSV_PATH,
                index=False
            )

            if prediction == "Positive":

                st.success(
                    "😊 POSITIVE REVIEW"
                )

            elif prediction == "Negative":

                st.error(
                    "😞 NEGATIVE REVIEW"
                )

            else:

                st.info(
                    "😐 NEUTRAL REVIEW"
                )

            st.success(
                "✅ Review saved in database!"
            )

            st.info(
                "📁 Database: freshcart.db"
            )

            st.write("")

            st.markdown(
                '<div class="section-title">📊 Updated Sentiment Graph</div>',
                unsafe_allow_html=True
            )

            sentiment_count = (
                data["Sentiment"]
                .value_counts()
            )

            st.bar_chart(
                sentiment_count
            )


# =========================================================
# ANALYTICS
# =========================================================

elif page == "📊 Analytics":

    st.markdown(
        '<div class="section-title">📊 Customer Feedback Analytics</div>',
        unsafe_allow_html=True
    )

    st.write("")

    # =========================
    # ML MODEL PERFORMANCE
    # =========================

    st.markdown(
        '<div class="section-title">🤖 ML Model Performance</div>',
        unsafe_allow_html=True
    )

    st.write("")

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Accuracy",
            "98.04%"
        )

    with m2:
        st.metric(
            "Precision",
            "98.23%"
        )

    with m3:
        st.metric(
            "Recall",
            "98.04%"
        )

    with m4:
        st.metric(
            "F1-Score",
            "98.07%"
        )

    st.write("")

    st.markdown("### 📌 Confusion Matrix")

    confusion_data = pd.DataFrame(
        [
            [19, 0, 0],
            [0, 21, 0],
            [2, 0, 60]
        ],
        columns=[
            "Positive",
            "Negative",
            "Neutral"
        ],
        index=[
            "Positive",
            "Negative",
            "Neutral"
        ]
    )

    st.dataframe(
        confusion_data,
        use_container_width=True
    )

    st.divider()

    # =========================
    # EXISTING ANALYTICS
    # =========================

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 📈 Sentiment Analysis")

        sentiment_count = (
            data["Sentiment"]
            .value_counts()
        )

        st.bar_chart(
            sentiment_count
        )

    with col2:

        st.markdown("### ⭐ Rating Analysis")

        rating_count = (
            data["Rating"]
            .value_counts()
            .sort_index()
        )

        st.bar_chart(
            rating_count
        )

    st.divider()

    st.markdown(
        '<div class="section-title">🥬 Product Categories</div>',
        unsafe_allow_html=True
    )

    category_count = (
        data["Category"]
        .value_counts()
    )

    st.bar_chart(
        category_count
    )


# =========================================================
# PRODUCTS
# =========================================================

elif page == "🛍️ Products":

    st.markdown(
        '<div class="section-title">🛍️ Grocery Products</div>',
        unsafe_allow_html=True
    )

    st.write("")

    # =========================
    # ADD PRODUCT
    # =========================

    st.markdown("### ➕ Add New Product")

    col1, col2 = st.columns(2)

    with col1:

        product_name = st.text_input(
            "Product Name",
            placeholder="Example: Amul Milk"
        )

        category = st.text_input(
            "Category",
            placeholder="Example: Dairy"
        )

    with col2:

        price = st.number_input(
            "Price (₹)",
            min_value=0.0,
            step=1.0
        )

        stock = st.number_input(
            "Stock",
            min_value=0,
            step=1
        )

    if st.button(
        "➕ Add Product",
        use_container_width=True
    ):

        if product_name.strip() == "":

            st.warning(
                "Please enter product name."
            )

        elif category.strip() == "":

            st.warning(
                "Please enter category."
            )

        else:

            add_product(
                product_name,
                category,
                price,
                stock
            )

            st.success(
                f"✅ {product_name} added successfully!"
            )

    st.divider()

    # =========================
    # SHOW PRODUCTS
    # =========================

    st.markdown("### 📋 Available Products")

    products = load_products()

    if len(products) > 0:

        st.dataframe(
            products,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No products added yet."
        )


# =========================
# FOOTER
# =========================

st.markdown("""
<div class="footer">

🛒 <b>FreshCart AI</b><br>
Online Grocery Product Feedback Analyzer<br><br>
Built using Python • Streamlit • Machine Learning

</div>
""", unsafe_allow_html=True)