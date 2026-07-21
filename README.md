# Retail Intelligence Platform

A production-style local data platform for retail analytics, built with Kafka, Spark, dbt, Airflow, FastAPI, Streamlit, and ML workflows.

This project simulates retail events in real time, transforms them into business-ready analytics tables, exposes the results through APIs, and presents them in an interactive dashboard.

## Why this project?

Many portfolio projects stop at one part of the data lifecycle: a dashboard, a batch job, or a machine learning notebook.

This project explores what happens when you connect the full system:

- event generation
- streaming ingestion
- schema validation
- medallion-style transformations
- workflow orchestration
- API serving
- dashboard consumption
- monitoring
- ML outputs

The goal is to show how raw retail activity can become usable business analytics through one working local platform.

## What the platform does

The system simulates an online retail business and produces:

- daily sales and revenue metrics
- top customer activity views
- inventory position analytics
- revenue forecasting
- churn risk scoring
- product recommendations

## Platform architecture

```text
Synthetic Event Producer
        ↓
      Kafka  ←→  Schema Registry
        ↓
 Spark Bronze Ingestion
        ↓
 Spark Silver Transformations
        ↓
 dbt Gold Models
        ↓
   FastAPI Endpoints
        ↓
 Streamlit Dashboard

Additional platform services:
- Airflow orchestrates the end-to-end workflow
- Prometheus + Grafana monitor service health
- MinIO provides object storage support
- PostgreSQL stores Airflow metadata
- ML jobs read Gold data and write forecasts/predictions
```

### Architecture in plain language

This project follows a simple business flow:

- **Python producers** generate synthetic retail events
- **Kafka** receives and distributes those events
- **Spark Bronze** stores the raw event stream
- **Spark Silver** cleans and structures the data into usable domain tables
- **dbt Gold** builds analytics-ready business models
- **FastAPI** exposes those results through REST APIs
- **Streamlit** displays KPIs, charts, and business views
- **Airflow** automates the pipeline
- **ML jobs** read Gold data and generate forecasts, churn scores, and recommendations

If you are not technical, you can think of it as a system that turns raw store activity into dashboards and insights automatically.

## Tech stack

| Layer | Tooling |
| --- | --- |
| Event generation | Python |
| Streaming | Kafka, Kafka UI |
| Contracts | Apicurio Schema Registry |
| Processing | PySpark, Delta Lake |
| Analytics engineering | dbt, Spark Thrift |
| Orchestration | Apache Airflow |
| Serving | FastAPI |
| Dashboard | Streamlit, Plotly |
| Machine learning | XGBoost, ALS recommendations, forecasting workflow |
| Monitoring | Prometheus, Grafana |
| Storage / metadata | MinIO, PostgreSQL |
| Deployment | Docker Compose |

## Production-style features

- **Event-driven ingestion** using Kafka topics for retail activity
- **Schema-aware ingestion** with registry-backed event contracts
- **Bronze / Silver / Gold architecture** for layered data processing
- **Analytics-ready marts** built with dbt
- **Workflow orchestration** with Airflow DAGs
- **REST serving layer** for downstream consumers
- **Interactive BI dashboard** for business-facing analytics
- **Monitoring stack** with Prometheus and Grafana
- **Integrated ML workflows** for forecasting, churn scoring, and recommendations
- **Containerized local platform** for reproducible execution

## Business outputs

### Gold analytics models

- `fct_daily_sales`
- `fct_customer_activity`
- `fct_inventory_position`

### ML outputs

- 30-day revenue forecast
- churn risk predictions
- product recommendations

## Dashboard and API

### Streamlit dashboard

- `http://localhost:8501`

The dashboard includes:

- revenue KPIs
- order metrics
- sales trend chart
- customer activity view
- inventory view
- ML insights
- pipeline overview

### FastAPI endpoints

Swagger UI:

- `http://localhost:8000/docs`

Example endpoints:

- `GET /sales/daily`
- `GET /customers/top`
- `GET /inventory/position`
- `GET /ml/forecast`
- `GET /ml/churn`
- `GET /ml/recommendations/{customer_id}`

## Local services

| Service | URL |
| --- | --- |
| Streamlit dashboard | `http://localhost:8501` |
| FastAPI docs | `http://localhost:8000/docs` |
| Airflow | `http://localhost:8082` |
| Kafka UI | `http://localhost:8081` |
| Schema Registry | `http://localhost:8083` |
| Grafana | `http://localhost:3000` |
| Prometheus | `http://localhost:9090` |
| MinIO Console | `http://localhost:9001` |

Default local credentials:

- Airflow: `admin` / `admin`
- Grafana: `admin` / `admin`
- MinIO: `minioadmin` / `minioadmin`

## Quick start

### 1. Start the platform

```powershell
docker compose up -d
```

### 2. Generate events

```powershell
docker compose --profile producers up producer
```

### 3. Build Bronze

```powershell
docker compose --profile spark up spark-bronze
```

### 4. Build Silver

```powershell
docker compose --profile spark up spark-silver
```

### 5. Build Gold

```powershell
docker compose --profile dbt up --build dbt
```

### 6. Run ML workflows

```powershell
docker compose --profile ml up --build ml-train
```

### 7. Open the dashboard

- `http://localhost:8501`

## Airflow orchestration

The project includes an Airflow DAG called `retail_pipeline` that orchestrates:

- event production
- quarantine demo injection
- Bronze ingestion
- Silver transformation
- Gold model build with dbt
- Gold validation
- ML training

Airflow UI:

- `http://localhost:8082`

## Data layers

### Bronze
Raw event data plus quarantine handling for invalid records.

### Silver
Cleaned domain tables for:

- customers
- products
- orders
- payments
- clicks
- inventory

### Gold
Business-ready marts used by the API, dashboard, and ML jobs.

## Example ML artifacts

Generated outputs include:

- `data/ml/forecasts/sales_forecast.parquet`
- `data/ml/models/churn_model.joblib`
- `data/ml/predictions/churn_scores.parquet`
- `data/ml/predictions/recommendations.parquet`

## Repository structure

```text
airflow/       DAGs and orchestration assets
contracts/     Event schemas and contracts
data/          Local Bronze, Silver, Gold, and ML outputs
data_quality/  Validation assets
dbt/           Gold analytics models
fastapi/       REST API
kafka/         Kafka image/configuration
ml/            ML training jobs
monitoring/    Prometheus and Grafana assets
producer/      Synthetic event generator
spark/         Bronze and Silver Spark jobs
streamlit/     BI dashboard
tests/         Automated tests
```

## What I learned

This project helped me practice:

- connecting multiple data tools into one working platform
- debugging cross-service integration issues
- turning event data into analytics-ready outputs
- serving data products through APIs and dashboards
- thinking end-to-end about data engineering workflows

## Notes

- The dataset is synthetic and intended for demonstration.
- The platform runs locally with Docker Compose.
- ML outputs are operational inside the project, but this is best described as a **data platform with integrated ML workflows**, not a full MLOps platform.

## Validation

Example validation commands:

```powershell
docker compose ps
python -m pytest
```

## Future improvements

Potential next steps:

- improve dashboard polish and UX
- add screenshots and architecture diagrams to the README
- add richer business dimensions and larger demo datasets
- strengthen ML versioning and experiment tracking
- expand automated data quality validation

---

