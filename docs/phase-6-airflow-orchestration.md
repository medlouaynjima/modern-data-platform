# Phase 6: Airflow Orchestration

Phase 6 adds Apache Airflow to orchestrate the retail lakehouse pipeline end to end.

## Pipeline DAG

The `retail_pipeline` DAG runs these tasks in order:

1. `produce_events` — publish synthetic retail events to Kafka
2. `bronze_ingestion` — Spark Streaming job writing Bronze Delta
3. `validate_bronze` — Great Expectations checks on Bronze events
4. `silver_transformation` — Spark batch job writing typed Silver Delta tables
5. `validate_silver` — Great Expectations checks on Silver tables
6. `wait_for_spark_thrift` — wait for Spark Thrift Server before dbt
7. `dbt_gold_build` — run `dbt build` for Gold analytics marts
8. `validate_gold` — Great Expectations checks on Gold marts

Each task retries twice with a two-minute delay.

## Airflow Services

| Service | Purpose |
| --- | --- |
| `airflow-init` | Migrates metadata DB and creates the local admin user |
| `airflow-webserver` | Airflow UI on port `8080` |
| `airflow-scheduler` | Executes scheduled and triggered DAG runs |
| `spark-thrift` | Shared Spark SQL endpoint required by dbt |

Airflow stores metadata in the PostgreSQL database `airflow`.

## Start Airflow

Start core infrastructure plus Airflow:

```powershell
docker compose up -d
docker compose --profile airflow up -d --build
```

Open the UI:

```powershell
start http://localhost:8080
```

Default credentials:

| Setting | Value |
| --- | --- |
| Username | `admin` |
| Password | `admin` |

## Trigger the Pipeline

From the Airflow UI:

1. Open the `retail_pipeline` DAG
2. Unpause the DAG
3. Click **Trigger DAG**

From the CLI:

```powershell
docker compose --profile airflow exec airflow-scheduler airflow dags trigger retail_pipeline
```

Or with Make:

```powershell
make pipeline
```

## Validate DAGs Locally

Install Airflow test dependencies:

```powershell
python -m pip install -r airflow/requirements.txt
python -m pytest tests/test_airflow_dags.py
```

## Notes

- Airflow tasks invoke sibling Docker Compose services through the mounted Docker socket.
- The DAG uses the same producer, Spark, and dbt service definitions as the manual runbook.
- On Windows and macOS, set `MDP_PROJECT_DIR` in `.env` to the absolute host path of this repo so Spark and dbt containers mount `data/` correctly when launched from Airflow.
- If PostgreSQL was created before Phase 6, create the Airflow database manually or reset the Postgres volume:

  ```powershell
  docker compose exec postgres psql -U mdp -d warehouse -c "CREATE DATABASE airflow;"
  ```
