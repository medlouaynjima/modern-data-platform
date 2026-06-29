from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DBT = ROOT / "dbt"


def test_dbt_project_files_exist():
    expected = [
        "dbt_project.yml",
        "profiles.yml",
        "Dockerfile",
        "macros/generate_schema_name.sql",
        "macros/silver_delta.sql",
        "models/staging/stg_customers.sql",
        "models/staging/stg_products.sql",
        "models/staging/stg_orders.sql",
        "models/staging/stg_payments.sql",
        "models/staging/stg_clicks.sql",
        "models/staging/stg_inventory.sql",
        "models/intermediate/int_orders_enriched.sql",
        "models/marts/fct_daily_sales.sql",
        "models/marts/fct_customer_activity.sql",
        "models/marts/fct_inventory_position.sql",
    ]

    missing = [path for path in expected if not (DBT / path).is_file()]

    assert missing == []


def test_staging_models_read_from_silver_delta_macro():
    staging_models = (DBT / "models" / "staging").glob("stg_*.sql")

    for model in staging_models:
        sql = model.read_text()

        assert "silver_delta(" in sql


def test_gold_models_depend_on_dbt_refs():
    gold_models = [
        DBT / "models" / "intermediate" / "int_orders_enriched.sql",
        DBT / "models" / "marts" / "fct_daily_sales.sql",
        DBT / "models" / "marts" / "fct_customer_activity.sql",
        DBT / "models" / "marts" / "fct_inventory_position.sql",
    ]

    for model in gold_models:
        sql = model.read_text()

        assert "ref(" in sql


def test_dbt_project_declares_gold_path_variable():
    project = (DBT / "dbt_project.yml").read_text()

    assert "silver_path:" in project
    assert "gold_path:" in project
