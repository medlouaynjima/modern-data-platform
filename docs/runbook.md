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

## Stop

```powershell
docker compose down
```

Use `docker compose down -v` only when you intentionally want to remove local Kafka, PostgreSQL, and MinIO state.
