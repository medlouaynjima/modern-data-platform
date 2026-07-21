import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Retail BI Dashboard", layout="wide", page_icon="🛍️")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .kpi-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 22px 20px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        color: white;
        margin-bottom: 10px;
    }
    .kpi-title { font-size: 0.85rem; color: #9a9ab8; letter-spacing: 0.05em; text-transform: uppercase; }
    .kpi-value { font-size: 2rem; font-weight: 700; color: #7c5cbf; margin-top: 6px; }
    .churn-high  { color: #ff6b6b; font-weight: 700; }
    .churn-med   { color: #ffd166; font-weight: 600; }
    .churn-low   { color: #06d6a0; font-weight: 600; }
    .section-header { font-size: 1.1rem; font-weight: 600; margin-bottom: 6px; color: #c9d1d9; }
</style>
""", unsafe_allow_html=True)

st.title("🛍️ Retail Business Intelligence")

API_URL = "http://fastapi:8000"

# ── Data fetchers ─────────────────────────────────────────────────────────────

# Gold endpoints query Spark Thrift which needs 20-40s to warm up after start.
# Use a 90s timeout so the first load doesn't fail during JVM warmup.
GOLD_TIMEOUT = 90
ML_TIMEOUT = 15

@st.cache_data(ttl=60)
def fetch_data(endpoint: str) -> pd.DataFrame:
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=GOLD_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data and isinstance(data[0], dict) and "error" in data[0]:
            st.warning(f"⚠️ API returned an error on `{endpoint}`: {data[0]['error']}")
            return pd.DataFrame()
        return pd.DataFrame(data)
    except requests.exceptions.Timeout:
        st.warning(
            f"⏳ `{endpoint}` timed out. Spark Thrift may still be warming up — "
            "wait 30 seconds and refresh the page."
        )
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Could not reach `{endpoint}`: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_forecast() -> pd.DataFrame:
    try:
        r = requests.get(f"{API_URL}/ml/forecast", timeout=ML_TIMEOUT)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception as e:
        st.warning(f"Could not fetch forecast: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_churn(limit: int = 50) -> pd.DataFrame:
    try:
        r = requests.get(f"{API_URL}/ml/churn?limit={limit}", timeout=ML_TIMEOUT)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception as e:
        st.warning(f"Could not fetch churn scores: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_recommendations(customer_id: str) -> pd.DataFrame:
    try:
        r = requests.get(f"{API_URL}/ml/recommendations/{customer_id}", timeout=ML_TIMEOUT)
        if r.status_code == 404:
            return pd.DataFrame()
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception as e:
        st.warning(f"Could not fetch recommendations: {e}")
        return pd.DataFrame()



st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Sales & Revenue",
    "👥 Customer Activity",
    "📦 Inventory",
    "🤖 ML Insights",
    "🗺️ Pipeline",
])

# ── Tab 1: Sales ──────────────────────────────────────────────────────────────
with tab1:
    with st.spinner("Loading sales data… (may take up to 90s on first load)"):
        df_sales = fetch_data("/sales/daily")

    # KPI row
    if not df_sales.empty:
        total_revenue = df_sales["total_sales_amount"].sum()
        total_orders  = df_sales["total_orders"].sum()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-title">Total Revenue (30 Days)</div>'
                f'<div class="kpi-value">${total_revenue:,.0f}</div></div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-title">Total Orders (30 Days)</div>'
                f'<div class="kpi-value">{total_orders:,.0f}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("")

    st.subheader("Daily Revenue Trend")
    if not df_sales.empty:
        df_sales = df_sales.sort_values("date")
        fig = px.line(
            df_sales, x="date", y="total_sales_amount",
            markers=True, line_shape="spline", render_mode="svg",
            color_discrete_sequence=["#7c5cbf"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9", xaxis_title="Date", yaxis_title="Revenue ($)",
        )
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("View Raw Sales Data"):
            st.dataframe(df_sales, use_container_width=True)
    else:
        st.info("No sales data available.")

# ── Tab 2: Customers ──────────────────────────────────────────────────────────
with tab2:
    with st.spinner("Loading customer data…"):
        df_customers = fetch_data("/customers/top")
    st.subheader("Top 10 Customers by Revenue")
    if not df_customers.empty:
        fig = px.bar(
            df_customers, x="customer_id", y="total_spent",
            color="total_spent", color_continuous_scale="Purples",
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
        )
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("View Customer Table"):
            st.dataframe(df_customers, use_container_width=True)
    else:
        st.info("No customer data available.")

# ── Tab 3: Inventory ──────────────────────────────────────────────────────────
with tab3:
    with st.spinner("Loading inventory data…"):
        df_inventory = fetch_data("/inventory/position")
    st.subheader("Recent Inventory Positions")
    if not df_inventory.empty:
        st.dataframe(df_inventory, use_container_width=True)
    else:
        st.info("No inventory data available.")

# ── Tab 4: ML Insights ────────────────────────────────────────────────────────
with tab4:
    st.subheader("🤖 ML Insights")
    st.caption(
        "Predictions are generated by the ML training pipeline. "
        "Run `docker compose --profile ml up ml-train` to refresh."
    )

    ml_tab1, ml_tab2, ml_tab3 = st.tabs([
        "📊 Sales Forecast",
        "⚠️ Churn Risk",
        "🎯 Recommendations",
    ])

    # ── ML Sub-tab 1: Sales Forecast ─────────────────────────────────────────
    with ml_tab1:
        st.markdown('<p class="section-header">30-Day Revenue Forecast (Prophet)</p>', unsafe_allow_html=True)
        df_forecast = fetch_forecast()

        if df_forecast.empty:
            st.info(
                "No forecast data available. "
                "Run `docker compose --profile ml up --build ml-train` to generate predictions."
            )
        else:
            df_forecast["date"] = pd.to_datetime(df_forecast["date"])
            df_hist = df_forecast[~df_forecast["is_forecast"]].copy()
            df_future = df_forecast[df_forecast["is_forecast"]].copy()

            fig = go.Figure()

            # Historical actuals
            fig.add_trace(go.Scatter(
                x=df_hist["date"], y=df_hist["forecast_revenue"],
                mode="lines", name="Historical",
                line=dict(color="#7c5cbf", width=2),
            ))

            # Forecast line
            fig.add_trace(go.Scatter(
                x=df_future["date"], y=df_future["forecast_revenue"],
                mode="lines", name="Forecast",
                line=dict(color="#f59e0b", width=2, dash="dot"),
            ))

            # Confidence band
            fig.add_trace(go.Scatter(
                x=pd.concat([df_future["date"], df_future["date"][::-1]]),
                y=pd.concat([df_future["forecast_upper"], df_future["forecast_lower"][::-1]]),
                fill="toself",
                fillcolor="rgba(245,158,11,0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="Confidence Interval",
            ))

            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#c9d1d9",
                legend=dict(orientation="h", y=-0.2),
                xaxis_title="Date", yaxis_title="Revenue ($)",
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)

            future_total = df_future["forecast_revenue"].sum()
            st.metric("Projected Revenue (Next 30 Days)", f"${future_total:,.0f}")

            with st.expander("View Forecast Data"):
                st.dataframe(df_forecast, use_container_width=True)

    # ── ML Sub-tab 2: Churn Risk ──────────────────────────────────────────────
    with ml_tab2:
        st.markdown('<p class="section-header">Customer Churn Risk (XGBoost)</p>', unsafe_allow_html=True)
        churn_limit = st.slider("Number of customers to display", 10, 100, 25, key="churn_limit")
        df_churn = fetch_churn(limit=churn_limit)

        if df_churn.empty:
            st.info(
                "No churn scores available. "
                "Run `docker compose --profile ml up --build ml-train` to generate predictions."
            )
        else:
            # Summary KPIs
            high_risk = (df_churn["churn_segment"] == "High Risk").sum()
            med_risk  = (df_churn["churn_segment"] == "Medium Risk").sum()
            low_risk  = (df_churn["churn_segment"] == "Low Risk").sum()

            k1, k2, k3 = st.columns(3)
            k1.metric("🔴 High Risk", f"{high_risk}")
            k2.metric("🟡 Medium Risk", f"{med_risk}")
            k3.metric("🟢 Low Risk", f"{low_risk}")

            # Churn score bar chart
            df_churn_sorted = df_churn.sort_values("churn_score", ascending=True).tail(20)
            color_map = {"High Risk": "#ff6b6b", "Medium Risk": "#ffd166", "Low Risk": "#06d6a0"}
            fig = px.bar(
                df_churn_sorted,
                x="churn_score", y="customer_id",
                orientation="h",
                color="churn_segment",
                color_discrete_map=color_map,
                title="Top 20 Highest-Risk Customers",
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#c9d1d9", xaxis_title="Churn Probability", yaxis_title="",
                legend_title="Risk Segment",
            )
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("View Full Churn Table"):
                st.dataframe(df_churn, use_container_width=True)

    # ── ML Sub-tab 3: Recommendations ────────────────────────────────────────
    with ml_tab3:
        st.markdown('<p class="section-header">Product Recommendations (Implicit ALS)</p>', unsafe_allow_html=True)

        # Offer a customer ID selector using churn data as the universe
        df_churn_all = fetch_churn(limit=200)
        if not df_churn_all.empty:
            customer_options = df_churn_all["customer_id"].tolist()
            selected_customer = st.selectbox(
                "Select a Customer ID", options=customer_options, key="rec_customer"
            )
        else:
            selected_customer = st.text_input("Enter a Customer ID", key="rec_customer_text")

        if selected_customer:
            df_recs = fetch_recommendations(str(selected_customer))
            if df_recs.empty:
                st.info(f"No recommendations found for customer `{selected_customer}`.")
            else:
                st.success(f"Top {len(df_recs)} recommended products for **{selected_customer}**")
                # Display as styled cards
                cols = st.columns(min(len(df_recs), 5))
                for i, (_, row) in enumerate(df_recs.iterrows()):
                    with cols[i % 5]:
                        score_pct = round(float(row.get("recommendation_score", 0)) * 100, 1)
                        name = row.get("product_name", row.get("product_id", "—"))
                        cat  = row.get("category", "")
                        st.markdown(
                            f'<div class="kpi-card">'
                            f'<div class="kpi-title">#{int(row["rank"])} · {cat}</div>'
                            f'<div class="kpi-value" style="font-size:1.1rem">{name}</div>'
                            f'<div class="kpi-title" style="margin-top:6px">Score: {score_pct}%</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                with st.expander("View Raw Recommendation Data"):
                    st.dataframe(df_recs, use_container_width=True)

# ── Tab 5: Pipeline overview ──────────────────────────────────────────────────
with tab5:
    st.subheader("How the Pipeline Works")
    st.caption("An interactive overview of the Bronze → Silver → Gold medallion architecture.")
    dashboard_path = Path(__file__).parent / "static" / "pipeline-dashboard.html"
    if dashboard_path.exists():
        components.html(dashboard_path.read_text(encoding="utf-8"), height=900, scrolling=True)
    else:
        st.error("Pipeline dashboard file not found at streamlit/static/pipeline-dashboard.html")
