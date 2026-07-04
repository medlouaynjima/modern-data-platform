# Modern Data Platform

A production-style data engineering portfolio project for ingesting, processing, storing, and serving retail business data.

The platform is built incrementally across **eleven phases**. Phases 1–9 are complete.

**Done (Phases 1–9):**

- Apache Kafka in KRaft mode, Kafka UI, PostgreSQL, MinIO, Apicurio Schema Registry
- Synthetic retail event producers with pre-publish contract checks
- Spark Streaming Bronze ingestion with pre-Bronze validation and quarantine
- Spark Silver transformations into typed Delta tables
- dbt Gold marts for sales, customer activity, and inventory
- Airflow orchestration for the end-to-end retail pipeline
- JSON Schema data contracts and Great Expectations post-layer validation
- Observability with Prometheus JMX scraping and a pre-built Grafana Pipeline Health dashboard
- FastAPI REST serving layer and Streamlit BI dashboard backed by the Gold Delta tables

**Planned (Phases 10–11):**
- ML pipeline (forecasting, churn, recommendations)
- Production engineering (CI/CD, integration tests, schema versioning)

See [docs/roadmap.md](docs/roadmap.md) for the full revised plan.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the system diagram and service notes.
See [docs/runbook.md](docs/runbook.md) for local operating commands.

```text
Producer → Kafka → Schema Registry → Validation → Bronze → Silver → dbt Gold
                                                                        ↓
                                                          FastAPI REST API
                                                                        ↓
                                                        Streamlit BI Dashboard
                                                                        ↓
                                                      Prometheus + Grafana (Observability)
```

## Quick Start

1. Copy environment defaults:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Start the core platform:

   ```powershell
   docker compose up -d
   ```

3. Check services:

   ```powershell
   docker compose ps
   ```

## Local Endpoints

| Service | URL |
| --- | --- |
| Kafka bootstrap | `localhost:29092` |
| Kafka UI | `http://localhost:8081` |
| PostgreSQL | `localhost:5432` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |
| Airflow UI | `http://localhost:8082` |
| Schema Registry | `http://localhost:8083` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |
| FastAPI (Swagger UI) | `http://localhost:8000/docs` |
| Streamlit BI Dashboard | `http://localhost:8501` |

Default credentials:
- MinIO: `minioadmin` / `minioadmin`
- Airflow: `admin` / `admin`
- Grafana: `admin` / `admin`
- PostgreSQL: see `.env.example`

## Kafka Topics

The stack creates the core retail event topics at startup:

- `customers`
- `products`
- `orders`
- `payments`
- `clicks`
- `inventory`

## Generate Events

Dry run without Kafka:

```powershell
python -m producer.main --events 2 --rate 0 --dry-run
```

Publish to Kafka after starting Docker Compose:

```powershell
python -m pip install -r producer/requirements.txt
python -m producer.main --bootstrap-server localhost:29092 --events 100 --rate 25
```

Containerized producer:

```powershell
docker compose --profile producers up producer
```

See [docs/phase-2-producers.md](docs/phase-2-producers.md).

## Ingest Bronze Data

After Kafka has events, run the Spark Bronze ingestion job:

```powershell
docker compose --profile spark up spark-bronze
```

Bronze Delta output is written under `data/bronze/events`.
See [docs/phase-3-bronze-streaming.md](docs/phase-3-bronze-streaming.md).

## Transform Silver Data

After Bronze data exists, run the Spark Silver transformation job:

```powershell
docker compose --profile spark up spark-silver
```

Silver Delta output is written under `data/silver/<topic>`.
See [docs/phase-4-silver-transformations.md](docs/phase-4-silver-transformations.md).

## Build Gold Models

After Silver data exists, run dbt against Spark:

```powershell
docker compose --profile dbt up --build dbt
```

Gold Delta output is written under `data/gold`.
See [docs/phase-5-dbt-gold-models.md](docs/phase-5-dbt-gold-models.md).

## Orchestrate with Airflow

Start Airflow and Spark Thrift:

```powershell
docker compose --profile airflow up -d --build
```

Trigger the full pipeline DAG:

```powershell
docker compose --profile airflow exec airflow-scheduler airflow dags trigger retail_pipeline
```

See [docs/phase-6-airflow-orchestration.md](docs/phase-6-airflow-orchestration.md).

## Validate Data Quality

After Silver or Gold data exists, run Great Expectations checkpoints:

```powershell
docker compose --profile ge up --build ge-bronze
docker compose --profile ge up --build ge-silver
docker compose --profile ge up --build ge-gold
```

See [docs/phase-7-great-expectations.md](docs/phase-7-great-expectations.md).

## Observability

Start Prometheus and Grafana:

```powershell
docker compose --profile monitoring up -d --build
```

- **Prometheus** at `http://localhost:9090` scrapes Kafka JMX metrics automatically.
- **Grafana** at `http://localhost:3000` has the **Pipeline Health** dashboard pre-loaded.

See [docs/phase-8-observability.md](docs/phase-8-observability.md).

## Serving Layer (API + BI)

Start the FastAPI REST API and Streamlit dashboard:

```powershell
docker compose --profile serving up -d --build
```

- **FastAPI Swagger UI** at `http://localhost:8000/docs` — browse and call the Gold data endpoints interactively.
- **Streamlit BI Dashboard** at `http://localhost:8501` — interactive KPI cards, revenue trends, top customer charts, and inventory views.

See [docs/phase-9-serving.md](docs/phase-9-serving.md).

## Repository Layout

```text
airflow/       Production DAGs and orchestration assets
consumer/      Streaming and batch consumers
data/          Local Bronze, Silver, and Gold development data
data_quality/  Great Expectations suites and validation CLI
dbt/           Analytics engineering models
docs/          Architecture, roadmap, and operating notes
fastapi/       FastAPI REST serving layer
kafka/         Kafka configuration and Dockerfile
ml/            Forecasting, recommendation, and fraud models
monitoring/    Prometheus and Grafana assets
producer/      Synthetic retail data generators
spark/         PySpark streaming and batch jobs
streamlit/     Streamlit BI dashboard
tests/         Unit and integration tests
```

## Development Commands

```powershell
make config   # Validate the Docker Compose configuration
make up       # Start local services
make ps       # Show service status
make logs     # Follow logs
make down     # Stop services
make bronze   # Run Spark Streaming to Bronze Delta
make silver   # Run Spark transformations to Silver Delta
make gold     # Run dbt models to Gold Delta
make airflow  # Start Airflow services
make pipeline # Trigger the retail_pipeline DAG
make validate-bronze # Run Great Expectations on Bronze events
make validate-silver # Run Great Expectations on Silver tables
make validate-gold   # Run Great Expectations on Gold marts
```

## Validation

```powershell
docker compose config
python -m pytest
```

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).
