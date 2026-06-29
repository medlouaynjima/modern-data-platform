# Phase 2: Data Generator and Kafka Producers

Phase 2 adds synthetic retail event generation for all Kafka topics created in Phase 1.

## Topics

| Topic | Event type |
| --- | --- |
| `customers` | Customer profile updates |
| `products` | Product catalog updates |
| `orders` | Order creation |
| `payments` | Payment authorization |
| `clicks` | Clickstream activity |
| `inventory` | Stock movement |

## Dry Run

Dry runs do not require Kafka:

```powershell
python -m producer.main --events 2 --rate 0 --dry-run
```

The `--events` value is per topic, so `--events 2` prints 12 records.

## Publish to Kafka

Start the platform first:

```powershell
docker compose up -d
```

Then run the producer from your local Python environment:

```powershell
python -m pip install -r producer/requirements.txt
python -m producer.main --bootstrap-server localhost:29092 --events 100 --rate 25
```

Or run the containerized producer:

```powershell
docker compose --profile producers up producer
```

Inspect messages in Kafka UI at `http://localhost:8080`.
