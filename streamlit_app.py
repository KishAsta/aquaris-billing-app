import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import uuid
from datetime import date

# =================================================
# CONFIG
# =================================================
st.set_page_config(page_title="Aquaris", layout="wide")
session = get_active_session()

# =================================================
# STYLES
# =================================================
st.markdown("""
<style>
.block-container { padding-top: 1rem; }
.brand { font-size: 28px; font-weight: 700; margin-bottom: 10px; }
.page-title { font-size: 32px; font-weight: 700; margin: 25px 0; }
.card {
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 25px;
}
.stButton > button {
    background-color: black;
    color: white;
    border-radius: 8px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# HEADER
# =================================================
st.markdown("<div class='brand'>Aquaris</div>", unsafe_allow_html=True)

# =================================================
# NAVIGATION (REAL)
# =================================================
tabs = st.tabs(["Home", "Billing", "Analytics", "Products"])

# =================================================
# HOME
# =================================================
with tabs[0]:
    st.markdown("<div class='page-title'>Home</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("<div class='card'><h3>A modern billing platform</h3><p>Aquaris is a lightweight billing and sales management platform designed to simplify invoice generation, offer application, and revenue tracking in one unified experience.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card'><h3>Built for speed and clarity</h3><p>Aquaris removes the complexity of manual billing by automating calculations, discounts, and bill generation while providing real-time visibility into sales performance.</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='card'><h3>Smart billing with insights</h3><p>With Aquaris, every bill contributes to live analytics—helping teams track revenue, monitor trends, and make informed decisions without switching tools.</p></div>", unsafe_allow_html=True)

# =================================================
# BILLING
# =================================================
with tabs[1]:
    st.markdown("<div class='page-title'>Billing</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    products_df = session.sql("SELECT * FROM PRODUCTS").to_pandas()
    offers_df = session.sql("SELECT * FROM OFFERS").to_pandas()

    cart = []

    for _, row in products_df.iterrows():
        qty = st.number_input(
            f"{row['PRODUCT_NAME']} (₹{row['PRICE']})",
            min_value=0,
            step=1,
            key=f"qty_{row['PRODUCT_ID']}"
        )
        if qty > 0:
            cart.append({
                "Product": row["PRODUCT_NAME"],
                "Qty": int(qty),
                "Price": float(row["PRICE"]),
                "Total": float(qty * row["PRICE"])
            })

    if not cart:
        st.info("Add products to generate bill")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    cart_df = pd.DataFrame(cart)
    subtotal = float(cart_df["Total"].sum())

    st.dataframe(cart_df, use_container_width=True)

    offer_codes = offers_df["OFFER_CODE"].tolist()
    selected_offer = st.selectbox("Apply Offer", ["None"] + offer_codes)

    discount = 0.0
    if selected_offer != "None":
        o = offers_df[offers_df["OFFER_CODE"] == selected_offer].iloc[0]
        if o["OFFER_TYPE"] == "FLAT":
            discount = float(o["OFFER_VALUE"])
        elif o["OFFER_TYPE"] == "PERCENT":
            discount = float(subtotal * o["OFFER_VALUE"] / 100)

    final_amount = float(subtotal - discount)

    st.metric("Final Amount", f"₹{final_amount:,.2f}")

    if st.button("Generate Bill"):
        session.sql(
            "INSERT INTO SALES VALUES (?, ?, ?, ?, ?)",
            params=[
                str(uuid.uuid4())[:8],
                date.today(),
                float(subtotal),
                float(discount),
                float(final_amount)
            ]
        ).collect()
        st.success("Bill generated successfully")

    st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# ANALYTICS
# =================================================
with tabs[2]:
    st.markdown("<div class='page-title'>Analytics</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    sales_df = session.sql(
        "SELECT BILL_DATE, FINAL_AMOUNT FROM SALES"
    ).to_pandas()

    if sales_df.empty:
        st.info("No sales data yet")
    else:
        daily_sales = sales_df.groupby("BILL_DATE")["FINAL_AMOUNT"].sum()
        st.bar_chart(daily_sales)

    st.markdown("</div>", unsafe_allow_html=True)

# =================================================
# PRODUCTS
# =================================================
with tabs[3]:
    st.markdown("<div class='page-title'>Products</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.dataframe(products_df, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
