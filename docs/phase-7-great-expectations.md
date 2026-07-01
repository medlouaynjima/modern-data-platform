# Phase 7: Data Contracts + Validation

Phase 7 enforces retail event contracts at the Kafka boundary and keeps post-layer Great Expectations checks for reconciliation.

## Components

| Component | Purpose |
| --- | --- |
| `contracts/schemas/*.json` | JSON Schema contracts per Kafka topic |
| `contracts/validator.py` | Schema + business rule validation |
| `contracts/registry.py` | Load schemas from files or Apicurio Registry |
| `schema-registry` | Apicurio Registry (JSON schemas) |
| `schema-registry-init` | Registers topic schemas on startup |
| Spark Bronze stream | Pre-Bronze gate with quarantine path |
| Producer | Validates events before publishing to Kafka |
| `data_quality/` | Post-layer GE checks on Bronze, Silver, Gold |

## Contract Rules

Every topic validates against JSON Schema plus business rules:

| Rule | Applies to |
| --- | --- |
| Required fields present | All topics |
| `timestamp` not in the future | All topics |
| `price > 0` | `orders`, `products` |
| `amount > 0` | `payments` |
| `order_id` unique within batch | `orders` |

Invalid events are **quarantined** to `data/bronze/quarantine/events` with a `validation_errors` column instead of landing in Bronze.

## Pipeline Flow

```text
Producer (contract check)
    ↓
Kafka
    ↓
Schema Registry (Apicurio)
    ↓
Spark Bronze (contract check + quarantine split)
    ↓
GE validate_bronze (post-layer reconciliation)
    ↓
Silver → validate_silver → Gold → validate_gold
```

## Start Schema Registry

Schema registry starts with core infrastructure:

```powershell
docker compose up -d
docker compose ps schema-registry
```

Register or refresh schemas:

```powershell
docker compose up schema-registry-init
```

UI: `http://localhost:8083` (default `SCHEMA_REGISTRY_PORT`)

## Run Validation

Producer dry-run with contract preview:

```powershell
python -m pip install -r contracts/requirements.txt
python -m producer.main --events 2 --rate 0 --dry-run
```

Bronze ingestion with pre-Bronze validation:

```powershell
docker compose --profile spark up --build spark-bronze
```

Post-layer GE checks:

```powershell
make validate-bronze
make validate-silver
make validate-gold
```

Inspect quarantined records:

```powershell
Get-ChildItem -Recurse data/bronze/quarantine
```

## Airflow Integration

The `retail_pipeline` DAG runs:

1. `produce_events`
2. `inject_quarantine_demo` (invalid Kafka records for quarantine testing)
3. `bronze_ingestion` (includes pre-Bronze contract validation)
3. `validate_bronze` (GE reconciliation)
4. `silver_transformation`
5. `validate_silver`
6. `dbt_gold_build`
7. `validate_gold`

## Project Layout

```text
contracts/
  schemas/          JSON Schema per topic
  validator.py      Contract validation engine
  registry.py       File + Apicurio schema loader
schema_registry/
  register_schemas.py
  Dockerfile
data_quality/       Post-layer Great Expectations
```
