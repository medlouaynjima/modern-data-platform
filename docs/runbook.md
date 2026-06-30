# Local Runbook

## Start

```powershell
Copy-Item .env.example .env
docker compose up -d
docker compose ps
```

## Verify

Kafka topics:

```powershell
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list
```

PostgreSQL schemas:

```powershell
docker compose exec postgres psql -U mdp -d warehouse -c "\dn"
```

MinIO bucket:

```powershell
docker compose run --rm minio-bootstrap
```

Producer dry run:

```powershell
python -m producer.main --events 2 --rate 0 --dry-run
```

Publish sample events:

```powershell
docker compose --profile producers up producer
```

Run Bronze ingestion:

```powershell
docker compose --profile spark up spark-bronze
```

Inspect Bronze files:

```powershell
Get-ChildItem -Recurse data/bronze/events
```

Run Silver transformations:

```powershell
docker compose --profile spark up spark-silver
```

Inspect Silver files:

```powershell
Get-ChildItem -Recurse data/silver
```

Run Gold dbt models:

```powershell
docker compose --profile dbt up --build dbt
```

Inspect Gold files:

```powershell
Get-ChildItem -Recurse data/gold
```

Start Airflow:

```powershell
docker compose --profile airflow up -d --build
```

Trigger the pipeline DAG:

```powershell
docker compose --profile airflow exec airflow-scheduler airflow dags trigger retail_pipeline
```

## Stop

```powershell
docker compose down
```

Use `docker compose down -v` only when you intentionally want to remove local Kafka, PostgreSQL, and MinIO state.
