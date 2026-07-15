# Phase 10 — ML Layer

Three machine learning models that consume Gold Delta tables and write predictions back to the platform.

## Architecture

```text
Gold Delta Tables
    ├── fct_daily_sales          → Prophet Forecast   → data/ml/forecasts/sales_forecast.parquet
    ├── fct_customer_activity    → XGBoost Churn      → data/ml/predictions/churn_scores.parquet
    └── fct_customer_activity    → Implicit ALS Recs  → data/ml/predictions/recommendations.parquet
                                                              ↓
                                                    FastAPI /ml/* endpoints
                                                              ↓
                                                    Streamlit ML Insights tab
```

## Models

### Model 1 — Sales Forecasting (Prophet)

| Property | Detail |
|---|---|
| Script | `ml/train_forecast.py` |
| Input | `fct_daily_sales` — daily aggregated `gross_revenue` |
| Algorithm | Meta Prophet (additive time-series with weekly + yearly seasonality) |
| Output | 30-day forecast with `forecast_revenue`, `forecast_lower`, `forecast_upper` |
| Sink | `data/ml/forecasts/sales_forecast.parquet` |

### Model 2 — Customer Churn Prediction (XGBoost)

| Property | Detail |
|---|---|
| Script | `ml/train_churn.py` |
| Input | `fct_customer_activity` — per-customer RFM aggregates |
| Features | `total_orders`, `total_revenue`, `total_sessions`, `days_since_last_order`, `order_frequency`, `revenue_per_order`, `click_to_order_ratio` |
| Label | Customers with ≥1 past order but no activity in last 14 days |
| Algorithm | XGBoostClassifier (200 estimators, depth 4, LR 0.05) |
| Output | `customer_id`, `churn_score`, `churn_segment` (Low / Medium / High Risk) |
| Sink | `data/ml/predictions/churn_scores.parquet` |

### Model 3 — Product Recommendations (Implicit ALS)

| Property | Detail |
|---|---|
| Script | `ml/train_recommendations.py` |
| Input | `fct_customer_activity` + `fct_daily_sales` (implicit feedback matrix) |
| Algorithm | Alternating Least Squares collaborative filtering (`implicit` library) |
| Factors | 50 latent factors, 20 iterations |
| Output | Top-5 `product_id` recommendations per customer with `rank` and `recommendation_score` |
| Sink | `data/ml/predictions/recommendations.parquet` |

## Running the ML Pipeline

### Manual (one-shot)

```powershell
docker compose --profile ml up --build ml-train
```

This trains all three models in sequence and writes prediction parquets to `data/ml/`.

### Via Airflow (automated, daily)

The `retail_pipeline` DAG has an `ml_training` task wired after `validate_gold`.
Once the platform is running under the `airflow` profile, ML predictions are refreshed daily automatically.

```powershell
docker compose --profile airflow up -d --build
docker compose --profile airflow exec airflow-scheduler airflow dags trigger retail_pipeline
```

## Serving Predictions

FastAPI exposes three new endpoints:

| Endpoint | Description |
|---|---|
| `GET /ml/forecast` | Full sales forecast DataFrame (historical + 30-day future) |
| `GET /ml/churn?limit=50` | Top at-risk customers sorted by churn probability |
| `GET /ml/recommendations/{customer_id}` | Top-5 product recommendations for a customer |

Browse and test at **http://localhost:8000/docs**.

## Streamlit ML Insights Tab

Open **http://localhost:8501** and select the **🤖 ML Insights** tab. It contains three sub-tabs:

- **📊 Sales Forecast** — Plotly chart showing historical revenue + 30-day Prophet forecast with confidence band + projected revenue metric card
- **⚠️ Churn Risk** — Risk segment KPI cards + horizontal bar chart of the highest-risk customers
- **🎯 Recommendations** — Customer ID selector → top-5 recommended product cards

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GOLD_PATH` | `/opt/spark/work-dir/data/gold/fct_daily_sales` | Path to daily sales Delta table |
| `GOLD_PATH_CUSTOMERS` | `/opt/spark/work-dir/data/gold/fct_customer_activity` | Path to customer activity Delta table |
| `ML_OUTPUT_PATH` | `/opt/spark/work-dir/data/ml` | Root directory for ML outputs |
| `FORECAST_DAYS` | `30` | Number of future days to forecast |
| `CHURN_DAYS_THRESHOLD` | `14` | Days of inactivity before a customer is labelled churned |
| `RECOMMENDATION_TOP_N` | `5` | Number of recommendations per customer |
