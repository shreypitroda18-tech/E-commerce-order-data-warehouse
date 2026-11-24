import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------

st.set_page_config(
    page_title="E-Commerce Data Warehouse",
    page_icon="🛒",
    layout="wide"
)

# --------------------------------
# 2. DATABASE CONNECTION
# --------------------------------

@st.cache_resource
def connect_database():

    database_url = st.secrets["DATABASE_URL"]

    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

    return create_engine(database_url)

try:
    engine = connect_database()

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

except Exception as e:
    st.error("Database connection failed!")
    st.code(str(e))
    st.stop()

# --------------------------------
# 3. WEBSITE HEADER
# --------------------------------

st.title("🛒 E-Commerce Data Warehouse")

st.write(
    "Sales, Orders, Customers and Product Analytics"
)

st.divider()

# --------------------------------
# 4. FETCH DASHBOARD INFORMATION
# --------------------------------

try:
    with engine.connect() as conn:

        revenue = pd.read_sql(
            text("""
                SELECT COALESCE(SUM(total_amount), 0) AS total
                FROM fact_sales
            """),
            conn
        ).iloc[0, 0]

        total_orders = pd.read_sql(
            text("""
                SELECT COUNT(DISTINCT order_id) AS total
                FROM fact_sales
            """),
            conn
        ).iloc[0, 0]

        total_customers = pd.read_sql(
            text("""
                SELECT COUNT(DISTINCT customer_id) AS total
                FROM fact_sales
            """),
            conn
        ).iloc[0, 0]

        products_sold = pd.read_sql(
            text("""
                SELECT COALESCE(SUM(quantity), 0) AS total
                FROM fact_sales
            """),
            conn
        ).iloc[0, 0]

except Exception as e:
    st.error("Could not load dashboard data.")
    st.code(str(e))
    st.stop()

# --------------------------------
# 5. KPI CARDS
# --------------------------------

st.subheader("📊 Business Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Revenue",
    f"₹{revenue:,.0f}"
)

col2.metric(
    "Total Orders",
    f"{total_orders:,}"
)

col3.metric(
    "Total Customers",
    f"{total_customers:,}"
)

col4.metric(
    "Products Sold",
    f"{products_sold:,}"
)

st.divider()

# --------------------------------
# 6. MONTHLY SALES CHART
# --------------------------------

st.subheader("📈 Monthly Sales Analysis")

with engine.connect() as conn:

    monthly_sales = pd.read_sql(
        text("""
            SELECT
                d.year,
                d.month,
                SUM(f.total_amount) AS revenue
            FROM fact_sales f
            JOIN dim_date d
            ON f.date_id = d.date_id
            GROUP BY d.year, d.month
            ORDER BY d.year, d.month
        """),
        conn
    )

if not monthly_sales.empty:

    monthly_sales["Month"] = (
        monthly_sales["year"].astype(str)
        + "-"
        + monthly_sales["month"].astype(str).str.zfill(2)
    )

    st.bar_chart(
        monthly_sales.set_index("Month")["revenue"]
    )

else:
    st.info("No monthly sales data available.")

st.divider()

# --------------------------------
# 7. TOP SELLING PRODUCTS
# --------------------------------

st.subheader("🏆 Top Selling Products")

with engine.connect() as conn:

    product_data = pd.read_sql(
        text("""
            SELECT
                p.product_name,
                p.category,
                SUM(f.quantity) AS quantity_sold,
                SUM(f.total_amount) AS revenue
            FROM fact_sales f
            JOIN dim_products p
            ON f.product_id = p.product_id
            GROUP BY p.product_id, p.product_name, p.category
            ORDER BY revenue DESC
        """),
        conn
    )

st.dataframe(
    product_data,
    use_container_width=True,
    hide_index=True
)

st.divider()

# --------------------------------
# 8. CUSTOMER ACTIVITY
# --------------------------------

st.subheader("👥 Customer Activity")

with engine.connect() as conn:

    customer_data = pd.read_sql(
        text("""
            SELECT
                c.customer_name,
                c.city,
                COUNT(DISTINCT f.order_id) AS total_orders,
                SUM(f.total_amount) AS total_spent
            FROM fact_sales f
            JOIN dim_customers c
            ON f.customer_id = c.customer_id
            GROUP BY c.customer_id, c.customer_name, c.city
            ORDER BY total_spent DESC
        """),
        conn
    )

st.dataframe(
    customer_data,
    use_container_width=True,
    hide_index=True
)

st.divider()

# --------------------------------
# 9. PAYMENT STATUS
# --------------------------------

st.subheader("💳 Payment Analysis")

with engine.connect() as conn:

    payment_data = pd.read_sql(
        text("""
            SELECT
                payment_status,
                COUNT(*) AS total_payments
            FROM dim_payments
            GROUP BY payment_status
        """),
        conn
    )

if not payment_data.empty:

    st.bar_chart(
        payment_data.set_index("payment_status")
    )

else:
    st.info("No payment information available.")

st.divider()

# --------------------------------
# 10. FOOTER
# --------------------------------

st.success("Dashboard loaded successfully!")

st.caption(
    "E-Commerce Orders Data Warehouse | "
    "Powered by Python, PostgreSQL and Streamlit"
)
