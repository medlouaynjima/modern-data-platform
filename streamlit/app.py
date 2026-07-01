import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Dashboard Config
st.set_page_config(page_title="Retail BI Dashboard", layout="wide", page_icon="🛍️")

# Custom CSS for aesthetic improvements
st.markdown("""
<style>
    .reportview-container { background: #f0f2f6; }
    .kpi-card {
        background-color: #2b2b2b;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        color: white;
    }
    .kpi-title { font-size: 1.2rem; color: #a9a9a9; }
    .kpi-value { font-size: 2rem; font-weight: bold; color: #4CAF50; }
</style>
""", unsafe_allow_html=True)

st.title("🛍️ Retail Business Intelligence")

API_URL = "http://fastapi:8000"

@st.cache_data(ttl=60)
def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_URL}{endpoint}")
        response.raise_for_status()
        data = response.json()
        if data and "error" in data[0]:
            st.error(f"API Error: {data[0]['error']}")
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data from {endpoint}: {e}")
        return pd.DataFrame()

# Fetch data
df_sales = fetch_data("/sales/daily")
df_customers = fetch_data("/customers/top")
df_inventory = fetch_data("/inventory/position")

# Top KPI Section
if not df_sales.empty:
    total_revenue = df_sales['total_sales_amount'].sum()
    total_orders = df_sales['total_orders'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Revenue (30 Days)</div><div class="kpi-value">${total_revenue:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Orders (30 Days)</div><div class="kpi-value">{total_orders:,.0f}</div></div>', unsafe_allow_html=True)
    with col3:
        if not df_customers.empty:
            top_customer = df_customers.iloc[0]['customer_id']
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Top Customer</div><div class="kpi-value">{top_customer}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Main Dashboard Content
tab1, tab2, tab3 = st.tabs(["📈 Sales & Revenue", "👥 Customer Activity", "📦 Inventory"])

with tab1:
    st.subheader("Daily Revenue Trend")
    if not df_sales.empty:
        # Sort by date for proper charting
        df_sales = df_sales.sort_values(by="date")
        fig = px.line(df_sales, x='date', y='total_sales_amount', markers=True, 
                      line_shape="spline", render_mode="svg")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("View Raw Sales Data"):
            st.dataframe(df_sales, use_container_width=True)

with tab2:
    st.subheader("Top 10 Customers by Revenue")
    if not df_customers.empty:
        fig = px.bar(df_customers, x='customer_id', y='total_spent', color='total_spent', 
                     color_continuous_scale="Viridis")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("View Customer Table"):
            st.dataframe(df_customers, use_container_width=True)

with tab3:
    st.subheader("Recent Inventory Positions")
    if not df_inventory.empty:
        st.dataframe(df_inventory, use_container_width=True)
