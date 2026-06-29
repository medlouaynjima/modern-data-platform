# Modern Data Platform

A production-style data engineering portfolio project for ingesting, processing, storing, and serving retail business data.

The platform is built incrementally across ten phases. Phase 1 provides the local infrastructure foundation:

- Apache Kafka in KRaft mode
- Kafka UI
- PostgreSQL warehouse
- MinIO S3-compatible object storage
- Lakehouse folder structure for Bronze, Silver, and Gold layers

## Architecture

See [docs/architecture.md](docs/architecture.md) for the system diagram and service notes.
See [docs/runbook.md](docs/runbook.md) for local operating commands.

## Quick Start

1. Copy environment defaults:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Start the platform:

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
| Kafka UI | `http://localhost:8080` |
| PostgreSQL | `localhost:5432` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |

Default MinIO credentials are `minioadmin` / `minioadmin`. Default PostgreSQL credentials are in `.env.example`.

## Kafka Topics

The stack creates the core retail event topics at startup:

- `customers`
- `products`
- `orders`
- `payments`
- `clicks`
- `inventory`

## Repository Layout

```text
airflow/       Production DAGs and orchestration assets
consumer/      Streaming and batch consumers
data/          Local Bronze, Silver, and Gold development data
dbt/           Analytics engineering models
docs/          Architecture, roadmap, and operating notes
fastapi/       Serving API
kafka/         Kafka configuration and topic documentation
ml/            Forecasting, recommendation, and fraud models
monitoring/    Prometheus and Grafana assets
producer/      Synthetic retail data generators
spark/         PySpark streaming and batch jobs
streamlit/     Analytics dashboard
tests/         Unit and integration tests
```

## Development Commands

```powershell
make config   # Validate the Docker Compose configuration
make up       # Start local services
make ps       # Show service status
make logs     # Follow logs
make down     # Stop services
```

## Validation

```powershell
docker compose config
python -m pytest
```

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).
