# Phase 4: Spark Transformations to Silver Delta Lake

Phase 4 reads raw Bronze Delta events, parses each topic payload, and writes typed Silver Delta tables.

## Silver Contract

Silver keeps business fields from each event payload and adds lineage back to Kafka and Bronze.

| Table path | Business grain |
| --- | --- |
| `data/silver/customers` | Customer profile update event |
| `data/silver/products` | Product catalog update event |
| `data/silver/orders` | Order created event |
| `data/silver/payments` | Payment authorization event |
| `data/silver/clicks` | Customer clickstream event |
| `data/silver/inventory` | Inventory adjustment event |

Every table includes:

| Column | Description |
| --- | --- |
| `event_id` | Producer event identifier |
| `event_type` | Retail event type |
| `event_timestamp` | Timestamp from the event payload |
| `event_date` | Partition date derived from `event_timestamp` |
| `source_topic` | Kafka source topic |
| `source_partition` | Kafka partition |
| `source_offset` | Kafka offset |
| `kafka_timestamp` | Kafka broker timestamp |
| `kafka_timestamp_type` | Kafka timestamp type |
| `event_key` | Kafka record key |
| `bronze_ingested_at` | Bronze ingestion timestamp |
| `bronze_ingest_date` | Bronze partition date |
| `silver_processed_at` | Silver processing timestamp |

## Run

Create Bronze data first:

```powershell
docker compose up -d
docker compose --profile producers up producer
docker compose --profile spark up spark-bronze
```

Run the Silver transformation:

```powershell
docker compose --profile spark up spark-silver
```

Or with Make:

```powershell
make silver
```

By default, the job overwrites each Silver table so it can be rerun safely from Bronze.

## Inspect Output

After a successful run, Silver Delta files should exist under:

```powershell
Get-ChildItem -Recurse data/silver
```
