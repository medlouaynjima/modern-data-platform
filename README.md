# Modern Data Platform

A local end-to-end retail analytics platform built to simulate how modern data systems ingest events, transform them into analytics tables, and serve insights through APIs and dashboards.

This project generates synthetic retail events, processes them through a Kafka + Spark + dbt + Airflow pipeline, exposes the results through FastAPI, and presents them in a Streamlit dashboard. It also includes ML workflows for forecasting, churn scoring, and product recommendations.

## Why this project matters

This project demonstrates practical experience with:

- event-driven data ingestion
- medallion-style data architecture (Bronze, Silver, Gold)
- analytics engineering with dbt
- workflow orchestration with Airflow
- API serving with FastAPI
- dashboarding with Streamlit
- monitoring with Prometheus and Grafana
- containerized local deployment with Docker Compose

In short, it shows how raw retail events can become business-ready analytics and ML outputs in one working platform.

## What the platform does

The pipeline simulates an online retail business:

1. synthetic customer, product, order, payment, click, and inventory events are generated
2. events are published to Kafka
3. Spark ingests them into a Bronze layer and quarantines invalid records
4. Spark transforms valid records into structured Silver tables
5. dbt builds Gold analytics marts for reporting
6. FastAPI serves business endpoints from the Gold layer
7. Streamlit displays KPIs and charts
8. ML jobs generate forecasts, churn scores, and recommendations

## Architecture

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

This project follows a simple flow:

- **Python producers** generate synthetic retail events
- **Kafka** receives and distributes those events
- **Spark Bronze** stores the raw event data
- **Spark Silver** cleans and structures the data into usable tables
- **dbt Gold** builds business-ready analytics models
- **FastAPI** exposes those results through REST endpoints
- **Streamlit** displays the outputs as charts, KPIs, and tables
- **Airflow** automates the full pipeline
- **ML jobs** read the Gold data and produce forecasts, churn scores, and recommendations

If you are not technical, you can think of it as a system that turns raw store activity into dashboards and insights automatically.

## Main technologies

| Area | Tools |
| --- | --- |
| Event streaming | Kafka, Kafka UI |
| Contracts | Apicurio Schema Registry |
| Processing | PySpark, Delta Lake |
| Analytics engineering | dbt, Spark Thrift |
| Orchestration | Apache Airflow |
| Serving | FastAPI |
| Dashboard | Streamlit |
| ML workflows | Prophet-style forecasting fallback, XGBoost, Implicit ALS |
| Monitoring | Prometheus, Grafana |
| Storage / metadata | MinIO, PostgreSQL |
| Deployment | Docker Compose |

## Business outputs

The working platform produces:

- daily sales and revenue metrics
- top customer views
- inventory position views
- 30-day revenue forecast
- customer churn risk scoring
- product recommendations

## API endpoints

Example FastAPI endpoints:

- `GET /sales/daily`
- `GET /customers/top`
- `GET /inventory/position`
- `GET /ml/forecast`
- `GET /ml/churn`
- `GET /ml/recommendations/{customer_id}`

Swagger UI:

- `http://localhost:8000/docs`

## Dashboard

Streamlit dashboard:

- `http://localhost:8501`

The dashboard includes:

- revenue KPIs
- order metrics
- sales trend chart
- customer activity view
- inventory table
- ML insights
- pipeline overview

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

1. Start the platform:

```powershell
docker compose up -d
```

2. Generate events:

```powershell
docker compose --profile producers up producer
```

3. Build Bronze:

```powershell
docker compose --profile spark up spark-bronze
```

4. Build Silver:

```powershell
docker compose --profile spark up spark-silver
```

5. Build Gold:

```powershell
docker compose --profile dbt up --build dbt
```

6. Run ML workflows:

```powershell
docker compose --profile ml up --build ml-train
```

7. Open the dashboard:

- `http://localhost:8501`

## Airflow orchestration

The project includes an Airflow DAG called `retail_pipeline` that orchestrates the main workflow:

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
Raw ingested event data plus quarantine handling for invalid records.

### Silver
Cleaned and typed domain tables for:

- customers
- products
- orders
- payments
- clicks
- inventory

### Gold
Business-ready marts for:

- `fct_daily_sales`
- `fct_customer_activity`
- `fct_inventory_position`

## ML outputs

The ML layer reads Gold data and writes reusable artifacts:

- forecast parquet output
- churn model artifact
- churn prediction parquet output
- recommendation parquet output

Example output paths:

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
fastapi/       REST API
kafka/         Kafka image/configuration
ml/            ML training jobs
dbt/           Gold analytics models
monitoring/    Prometheus and Grafana assets
producer/      Synthetic event generator
spark/         Bronze and Silver Spark jobs
streamlit/     BI dashboard
tests/         Automated tests
```

## What I learned

This project helped me practice:

- connecting multiple data tools in one working system
- debugging cross-container filesystem and orchestration issues
- turning raw events into analytics-ready models
- serving data products through APIs and dashboards
- thinking end-to-end about data engineering, not just isolated scripts

## Notes

- The dataset is synthetic and intended for demonstration.
- This platform runs locally with Docker Compose.
- Some ML outputs use fallback behavior when certain library versions are incompatible, but the pipeline remains operational.

## Validation

Example validation commands:

```powershell
docker compose ps
python -m pytest
```

## Future improvements

Possible next steps:

- improve dashboard polish and UX
- add stronger ML versioning / experiment tracking
- expand automated data quality checks
- add richer business dimensions and larger demo datasets

---

If you are a recruiter, engineer, or hiring manager, this project is best understood as a practical portfolio example of a local modern data platform with integrated analytics and ML workflows.
