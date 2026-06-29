# Phase 3: Spark Streaming to Bronze Delta Lake

Phase 3 consumes the six retail Kafka topics and writes raw Bronze records as Delta files.

## Bronze Contract

Bronze preserves the original Kafka payload and adds ingestion metadata:

| Column | Description |
| --- | --- |
| `topic` | Kafka source topic |
| `partition` | Kafka partition |
| `offset` | Kafka offset |
| `kafka_timestamp` | Kafka event timestamp |
| `kafka_timestamp_type` | Kafka timestamp type |
| `event_key` | Kafka record key as text |
| `event_payload` | Raw JSON payload as text |
| `ingested_at` | Spark ingestion timestamp |
| `ingest_date` | Partition date |

Output path:

```text
data/bronze/events
```

Checkpoint path:

```text
data/bronze/_checkpoints/events
```

## Run

Start the platform and publish sample events:

```powershell
docker compose up -d
docker compose --profile producers up producer
```

Run Bronze ingestion once with Spark `availableNow`:

```powershell
docker compose --profile spark up spark-bronze
```

For a continuous stream:

```powershell
docker compose run --rm spark-bronze `
  --packages io.delta:delta-spark_2.12:3.2.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 `
  --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension `
  --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog `
  /opt/spark/work-dir/spark/bronze_stream.py `
  --bootstrap-server kafka:9092 `
  --continuous
```

## Inspect Output

After a successful run, Bronze Delta files should exist under:

```powershell
Get-ChildItem -Recurse data/bronze/events
```
