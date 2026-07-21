# 🛒 Retail Intelligence Platform

> A production-style local data platform for real-time retail analytics, built with Kafka, Apache Spark, dbt, Airflow, FastAPI, Streamlit, and integrated machine learning workflows.

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-000000.svg?logo=apachekafka\&logoColor=white)](https://kafka.apache.org/)
[![Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C.svg?logo=apachespark\&logoColor=white)](https://spark.apache.org/)
[![dbt](https://img.shields.io/badge/dbt-F15C2A.svg?logo=dbt\&logoColor=white)](https://www.getdbt.com/)
[![Airflow](https://img.shields.io/badge/Airflow-017CEE.svg?logo=apacheairflow\&logoColor=white)](https://airflow.apache.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg?logo=streamlit\&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/docker-2496ED.svg?logo=docker\&logoColor=white)](https://www.docker.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C.svg?logo=prometheus\&logoColor=white)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-F46800.svg?logo=grafana\&logoColor=white)](https://grafana.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Why this project?

Many data projects stop at a single stage of the data lifecycle: a dashboard, a batch pipeline, or a machine learning notebook.

This project explores what happens when the complete data journey is connected into one working platform:

> **Event Generation → Streaming → Data Lake → Transformation → Analytics → APIs → Dashboard → Machine Learning**

The platform simulates an online retail business and processes synthetic retail activity through a complete data engineering workflow.

The goal is to demonstrate how raw event data can be transformed into reliable, business-ready analytics and machine learning outputs using modern data platform technologies.

---

## 🚀 Platform Overview

The platform continuously simulates retail activity and processes events through a layered data architecture.

It produces:

* 📊 Daily sales and revenue analytics
* 👥 Customer activity insights
* 📦 Inventory position analytics
* 📈 30-day revenue forecasting
* 🎯 Customer churn risk scoring
* 🛍️ Personalized product recommendations

The resulting data products are exposed through REST APIs and presented through an interactive Streamlit dashboard.

---

## 🏗️ System Architecture

```text
                    Synthetic Retail Events
                              │
                              ▼
                    Python Event Producers
                              │
                              ▼
                 ┌─────────────────────────┐
                 │          Kafka          │
                 │   Event Streaming Bus   │
                 └────────────┬────────────┘
                              │
                              ▼
                    Schema Registry
                              │
                              ▼
                 ┌─────────────────────────┐
                 │      Spark Bronze       │
                 │   Raw Event Ingestion   │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │      Spark Silver       │
                 │ Cleaned Domain Tables   │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │        dbt Gold         │
                 │ Business-Ready Marts    │
                 └────────────┬────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
             FastAPI Serving       ML Workflows
                    │                   │
                    ▼                   ▼
             Streamlit BI         ML Predictions
              Dashboard           & Recommendations


        ┌─────────────────────────────────────────────┐
        │              Airflow Orchestration          │
        │        End-to-End Pipeline Automation       │
        └─────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────┐
        │              Monitoring Layer               │
        │          Prometheus + Grafana                │
        └─────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────┐
        │              Platform Services              │
        │      MinIO + PostgreSQL + Docker Compose    │
        └─────────────────────────────────────────────┘
```

---

## 🔄 End-to-End Data Flow

The platform follows a complete business data lifecycle:

### 1. Event Generation

Python producers simulate realistic online retail activity, including:

* customer events
* product interactions
* orders
* payments
* clicks
* inventory updates

### 2. Streaming Ingestion

Kafka acts as the central event streaming layer.

Events are published to Kafka topics and distributed to downstream processing jobs.

Schema Registry provides structured event contracts to support schema-aware ingestion.

### 3. Bronze Layer

Apache Spark ingests raw events into the Bronze layer.

The Bronze layer preserves the raw event data while handling invalid records through quarantine mechanisms.

### 4. Silver Layer

Spark transformations clean and structure the raw data into domain-oriented tables covering:

* customers
* products
* orders
* payments
* clicks
* inventory

### 5. Gold Layer

dbt transforms the Silver data into analytics-ready business models.

Key Gold models include:

* `fct_daily_sales`
* `fct_customer_activity`
* `fct_inventory_position`

### 6. Data Serving

FastAPI exposes analytics and machine learning outputs through REST endpoints.

### 7. Business Intelligence

Streamlit consumes the platform outputs and provides an interactive dashboard for monitoring retail performance and business KPIs.

### 8. Machine Learning

ML workflows consume Gold-layer data to generate:

* revenue forecasts
* churn risk scores
* product recommendations

### 9. Orchestration

Apache Airflow coordinates the end-to-end workflow, from data generation and ingestion to transformation, validation, and ML execution.

---

## 🛠️ Tech Stack

| Layer                 | Technology                |
| --------------------- | ------------------------- |
| Event Generation      | Python                    |
| Event Streaming       | Apache Kafka              |
| Event Contracts       | Apicurio Schema Registry  |
| Processing            | Apache Spark / PySpark    |
| Data Lake             | Delta Lake                |
| Analytics Engineering | dbt                       |
| Orchestration         | Apache Airflow            |
| API Serving           | FastAPI                   |
| Dashboard             | Streamlit + Plotly        |
| Machine Learning      | XGBoost, ALS, Forecasting |
| Monitoring            | Prometheus + Grafana      |
| Object Storage        | MinIO                     |
| Metadata Storage      | PostgreSQL                |
| Containerization      | Docker + Docker Compose   |

---

## ⚙️ Production-Style Features

### 🔄 Event-Driven Data Ingestion

Retail events are generated and streamed through Kafka topics, creating a realistic event-driven data pipeline.

### 🧾 Schema-Aware Data Contracts

Apicurio Schema Registry provides centralized event schemas and contracts for structured data ingestion.

### 🥉🥈🥇 Medallion Data Architecture

The platform follows a Bronze → Silver → Gold architecture:

* **Bronze:** Raw event data
* **Silver:** Cleaned and structured domain data
* **Gold:** Business-ready analytics models

### 📊 Analytics Engineering with dbt

dbt models transform processed data into reusable business-facing analytical datasets.

### ⏱️ Workflow Orchestration

Airflow automates the data lifecycle through a dedicated `retail_pipeline` DAG.

The workflow includes:

* event production
* quarantine demonstration
* Bronze ingestion
* Silver transformations
* Gold model generation
* Gold validation
* ML training

### 🚀 API Data Products

FastAPI provides programmatic access to analytics and ML outputs.

### 📈 Interactive Business Dashboard

Streamlit provides a business-facing interface for:

* revenue KPIs
* order metrics
* sales trends
* customer activity
* inventory insights
* ML predictions
* pipeline status

### 📡 Platform Monitoring

Prometheus and Grafana provide service-level monitoring across the local platform.

### 🤖 Integrated Machine Learning

ML workflows consume analytics-ready Gold data to generate business predictions and recommendations.

### 🐳 Reproducible Local Platform

The complete platform is containerized with Docker Compose, allowing all services to run together in a reproducible local environment.

---

## 📊 Business Outputs

### Gold Analytics Models

| Model                    | Purpose                             |
| ------------------------ | ----------------------------------- |
| `fct_daily_sales`        | Daily revenue and sales performance |
| `fct_customer_activity`  | Customer engagement and activity    |
| `fct_inventory_position` | Inventory position and availability |

### Machine Learning Outputs

| Output           | Description                          |
| ---------------- | ------------------------------------ |
| Revenue Forecast | 30-day revenue forecasting           |
| Churn Risk       | Customer churn probability scoring   |
| Recommendations  | Personalized product recommendations |

---

## 🖥️ Platform Interface

### Streamlit Dashboard

The Streamlit dashboard provides a unified business view of the retail platform.

Key dashboard sections include:

* Revenue KPIs
* Order metrics
* Sales trends
* Customer activity
* Inventory position
* Machine learning insights
* Pipeline overview

![Retail Intelligence Dashboard](assets/dashboard.png)

---

## 🔌 API Reference

### `GET /sales/daily`

Returns daily sales and revenue analytics.

### `GET /customers/top`

Returns top customer activity metrics.

### `GET /inventory/position`

Returns current inventory position analytics.

### `GET /ml/forecast`

Returns revenue forecasting results.

### `GET /ml/churn`

Returns customer churn risk predictions.

### `GET /ml/recommendations/{customer_id}`

Returns personalized product recommendations for a customer.

### FastAPI Swagger Documentation

```text
http://localhost:8000/docs
```

---

## 📡 Local Platform Services

| Service             | URL                          |
| ------------------- | ---------------------------- |
| Streamlit Dashboard | `http://localhost:8501`      |
| FastAPI Swagger     | `http://localhost:8000/docs` |
| Airflow             | `http://localhost:8082`      |
| Kafka UI            | `http://localhost:8081`      |
| Schema Registry     | `http://localhost:8083`      |
| Grafana             | `http://localhost:3000`      |
| Prometheus          | `http://localhost:9090`      |
| MinIO Console       | `http://localhost:9001`      |

### Default Local Credentials

| Service | Username     | Password     |
| ------- | ------------ | ------------ |
| Airflow | `admin`      | `admin`      |
| Grafana | `admin`      | `admin`      |
| MinIO   | `minioadmin` | `minioadmin` |

> ⚠️ These credentials are intended only for local development and demonstration.

---

## 🚀 Quick Start

### 1. Start the Platform

```powershell
docker compose up -d
```

### 2. Generate Retail Events

```powershell
docker compose --profile producers up producer
```

### 3. Build the Bronze Layer

```powershell
docker compose --profile spark up spark-bronze
```

### 4. Build the Silver Layer

```powershell
docker compose --profile spark up spark-silver
```

### 5. Build the Gold Layer

```powershell
docker compose --profile dbt up --build dbt
```

### 6. Run Machine Learning Workflows

```powershell
docker compose --profile ml up --build ml-train
```

### 7. Launch the Dashboard

Open:

```text
http://localhost:8501
```

---

## 🌬️ Airflow Orchestration

The platform includes an Airflow DAG named:

```text
retail_pipeline
```

The DAG coordinates the end-to-end workflow:

```text
Event Production
      ↓
Quarantine Handling
      ↓
Bronze Ingestion
      ↓
Silver Transformation
      ↓
Gold dbt Models
      ↓
Gold Validation
      ↓
ML Training
```

Airflow UI:

```text
http://localhost:8082
```

---

## 🗄️ Data Architecture

### 🥉 Bronze Layer

The Bronze layer stores raw event data received from the streaming pipeline.

It also demonstrates quarantine handling for invalid or rejected records.

### 🥈 Silver Layer

The Silver layer contains cleaned and structured domain-level data:

* customers
* products
* orders
* payments
* clicks
* inventory

### 🥇 Gold Layer

The Gold layer contains business-ready analytical models consumed by:

* FastAPI
* Streamlit
* ML workflows

---

## 🤖 Machine Learning Artifacts

The platform generates operational ML artifacts, including:

```text
data/ml/
├── forecasts/
│   └── sales_forecast.parquet
│
├── models/
│   └── churn_model.joblib
│
└── predictions/
    ├── churn_scores.parquet
    └── recommendations.parquet
```

These outputs are generated from the Gold analytics layer and integrated into the platform's API and dashboard.

---

## 📁 Repository Structure

```text
retail-intelligence-platform/
│
├── airflow/
│   └── DAGs and orchestration assets
│
├── contracts/
│   └── Event schemas and data contracts
│
├── data/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── ml/
│
├── data_quality/
│   └── Validation assets
│
├── dbt/
│   └── Gold analytics models
│
├── fastapi/
│   └── REST API
│
├── kafka/
│   └── Kafka configuration
│
├── ml/
│   └── Machine learning workflows
│
├── monitoring/
│   └── Prometheus and Grafana configuration
│
├── producer/
│   └── Synthetic retail event generator
│
├── spark/
│   ├── Bronze ingestion
│   └── Silver transformations
│
├── streamlit/
│   └── Business intelligence dashboard
│
├── tests/
│   └── Automated tests
│
├── docker-compose.yml
└── README.md
```

---

## 🧪 Validation

Check running services:

```powershell
docker compose ps
```

Run automated tests:

```powershell
python -m pytest
```

The platform can also be validated through:

* Kafka event flow
* Bronze/Silver/Gold data outputs
* dbt model execution
* Airflow DAG runs
* API responses
* Dashboard data
* ML artifact generation
* Prometheus/Grafana service metrics

---

## 🧠 What I Learned

Building this platform helped me develop practical experience in:

* designing end-to-end data engineering architectures
* connecting streaming, batch, and analytical workloads
* working with Kafka and event-driven ingestion
* implementing Bronze/Silver/Gold data layers
* building analytics models with dbt
* orchestrating multi-stage pipelines with Airflow
* exposing data products through REST APIs
* building business-facing analytics dashboards
* integrating machine learning into data platforms
* monitoring distributed local services
* debugging cross-service integration issues
* designing reproducible multi-container environments

---

## 📌 Project Scope

This project is intentionally designed as a **production-style local data platform**.

The dataset is synthetic and the platform runs locally using Docker Compose.

While the platform includes integrated machine learning workflows, it is best characterized as a:

> **Modern Data Platform with Integrated ML Workflows**

rather than a full MLOps platform.

The primary focus is on demonstrating the complete data lifecycle:

> **Streaming → Processing → Transformation → Analytics → Serving → Visualization → ML**

---

## 🔮 Future Improvements

Potential next steps include:

* 📊 Improve dashboard UX and visual polish
* 🖼️ Add architecture and platform screenshots
* 🧪 Expand automated data quality checks
* 📦 Add larger and more realistic demo datasets
* 🧠 Improve ML model evaluation and validation
* 📈 Add experiment tracking and ML model versioning
* 🔄 Introduce CI/CD for data and ML workflows
* ☁️ Deploy the platform to a cloud environment
* 🔐 Add authentication and secure API access
* 📡 Expand observability across data pipeline stages

---

## 📄 License

MIT
