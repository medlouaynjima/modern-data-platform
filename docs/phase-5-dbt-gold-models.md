# Phase 5: dbt Models to Gold

Phase 5 adds a dbt project that reads Silver Delta tables and builds Gold analytics models.

## dbt Runtime

The dbt project uses the Spark adapter through Spark Thrift Server.

| Component | Purpose |
| --- | --- |
| `spark-thrift` | Exposes Spark SQL with Delta support on port `10000` |
| `dbt` | Runs `dbt build` against the Spark Thrift endpoint |
| `dbt/macros/silver_delta.sql` | Resolves local Silver Delta paths |

Default paths:

| Variable | Default |
| --- | --- |
| `silver_path` | `/opt/spark/work-dir/data/silver` |
| `gold_path` | `/opt/spark/work-dir/data/gold` |

## Model Layers

Staging models normalize one Silver table each:

- `stg_customers`
- `stg_products`
- `stg_orders`
- `stg_payments`
- `stg_clicks`
- `stg_inventory`

Intermediate model:

- `int_orders_enriched`: joins orders to latest product attributes and payment rollups.

Gold marts:

| Model | Grain |
| --- | --- |
| `fct_daily_sales` | Day, product, country, channel |
| `fct_customer_activity` | Day, customer |
| `fct_inventory_position` | Product, warehouse |

## Run

Create Silver data first:

```powershell
docker compose up -d
docker compose --profile producers up producer
docker compose --profile spark up spark-bronze
docker compose --profile spark up spark-silver
```

Run dbt:

```powershell
docker compose --profile dbt up --build dbt
```

Or with Make:

```powershell
make gold
```

## Validate dbt Connectivity

```powershell
make dbt-debug
```

## Inspect Output

Gold Delta files are written under:

```powershell
Get-ChildItem -Recurse data/gold
```
