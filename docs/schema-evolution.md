# Schema Evolution Strategy

This document describes how the Modern Data Platform handles schema changes across every layer, and the procedures for rolling out schema updates safely.

## Overview

The platform has three distinct schema surfaces:

| Layer | Technology | Evolution Mechanism |
|---|---|---|
| Event schemas (Kafka) | JSON Schema + Apicurio Registry | Compatibility rules (BACKWARD / FORWARD) |
| Delta Lake tables (Bronze/Silver/Gold) | Delta Protocol | `mergeSchema` / `overwriteSchema` options |
| dbt Gold models | dbt schema.yml | Model rebuilds via `dbt run` |

---

## 1. Kafka Event Schemas (Apicurio Schema Registry)

### Compatibility Modes

| Mode | Description | Use When |
|---|---|---|
| `BACKWARD` | New schema can read data written with the previous schema | Adding optional fields |
| `FORWARD` | Previous schema can read data written with the new schema | Removing fields |
| `FULL` | Both backward and forward compatible | Renaming fields (avoid!) |
| `NONE` | No compatibility enforced | Breaking changes with full reprocessing |

### Procedure: Adding a new optional field

```bash
# 1. Update the JSON Schema file in contracts/schemas/<topic>.json
# 2. The new field MUST have a default value (backward compatibility)
# 3. Register the new version with the registry
docker compose --profile airflow exec airflow-scheduler \
  curl -X POST http://schema-registry:8080/apis/registry/v2/groups/retail-events/artifacts/<topic>/versions \
  -H "Content-Type: application/json" \
  -d @contracts/schemas/<topic>.json

# 4. Verify compatibility
curl http://localhost:8083/apis/registry/v2/groups/retail-events/artifacts/<topic>/versions
```

### Procedure: Breaking change (new required field or type change)

1. Create a new schema version with `NONE` compatibility
2. Drain the Kafka topic (let all consumers finish processing)
3. Update Bronze ingestion to handle both old and new payloads (transformation in `silver_transform.py`)
4. Re-register the schema under the old artifact ID with a new major version

---

## 2. Delta Lake Tables (Bronze / Silver / Gold)

Delta Lake handles schema evolution at the transaction level. The platform uses two modes:

### `mergeSchema` — safe, additive changes

Use for adding new columns. The table protocol merges the new columns into the existing schema.

```python
# In spark/silver_transform.py or spark/bronze_stream.py
frame.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(path)
```

**Safe for**: Adding nullable columns, widening column types (e.g., `int` → `long`).

### `overwriteSchema` — destructive, full rewrite

Use only when changing column types incompatibly or removing columns. This rewrites the entire table.

```python
frame.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(path)
```

> [!WARNING]
> `overwriteSchema` deletes all existing data. Always take a backup or use Delta's `RESTORE` command first.

### Rollback with Delta Time Travel

Delta Lake keeps a transaction log. To roll back to a previous version:

```python
from delta.tables import DeltaTable

dt = DeltaTable.forPath(spark, "/opt/spark/work-dir/data/silver/orders")

# List available versions
dt.history().select("version", "timestamp", "operation").show()

# Restore to version N
dt.restoreToVersion(N)
```

Or via SQL:
```sql
RESTORE TABLE delta.`/opt/spark/work-dir/data/silver/orders` TO VERSION AS OF 5;
```

### Vacuum (cleaning old versions)

Delta retains 7 days of history by default. To reclaim disk space:
```sql
VACUUM delta.`/opt/spark/work-dir/data/silver/orders` RETAIN 168 HOURS;
```

---

## 3. dbt Gold Models

dbt models are SQL views/tables regenerated on every `dbt run`. Schema changes are handled by updating the model SQL and `schema.yml` together.

### Procedure: Adding a column to a Gold mart

```bash
# 1. Edit the SQL in dbt/models/marts/<model>.sql
# 2. Add the new column + description to dbt/models/marts/schema.yml
# 3. Rebuild the Gold layer
docker compose --profile dbt up --build dbt

# 4. The FastAPI and ML layers read from the Delta files directly;
#    they will pick up the new column automatically on next request / training run.
```

### Breaking change (removing or renaming a column)

1. Update the dbt model SQL
2. Update `schema.yml`
3. Update any downstream FastAPI queries in `fastapi/main.py` that reference the old column name
4. Update any ML feature engineering in `ml/train_churn.py` or `ml/train_recommendations.py`
5. Rebuild in order: `dbt` → `fastapi` → `ml-train`

---

## 4. Version Numbering Convention

| Change Type | Example | Version Bump |
|---|---|---|
| Add optional field | New nullable column | Minor (`v1.1`) |
| Remove field | Drop unused column | Major (`v2.0`) |
| Rename field | `user_id` → `customer_id` | Major (`v2.0`) |
| Type widening | `int` → `long` | Patch (`v1.0.1`) |
| Type narrowing | `string` → `int` | Major (`v2.0`) |

Track schema versions in `contracts/schemas/<topic>.json` using the `$schema` metadata field and register each version in Apicurio before deploying.
