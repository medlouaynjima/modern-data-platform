from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DAGS_FOLDER = ROOT / "airflow" / "dags"


def _import_dag_bag():
    original_path = sys.path.copy()
    sys.path = [path for path in sys.path if Path(path).resolve() != ROOT.resolve()]

    try:
        pytest.importorskip("airflow")

        from airflow.models import DagBag

        os.environ.setdefault("AIRFLOW__CORE__UNIT_TEST_MODE", "True")
        return DagBag(dag_folder=str(DAGS_FOLDER), include_examples=False)
    finally:
        sys.path = original_path


@pytest.fixture(scope="module")
def dag_bag():
    return _import_dag_bag()


def test_dags_load_without_import_errors(dag_bag) -> None:
    assert dag_bag.import_errors == {}, f"DAG import errors: {dag_bag.import_errors}"


def test_retail_pipeline_dag_exists(dag_bag) -> None:
    assert "retail_pipeline" in dag_bag.dags


def test_retail_pipeline_task_chain(dag_bag) -> None:
    dag = dag_bag.get_dag("retail_pipeline")
    assert dag is not None

    expected_tasks = {
        "produce_events",
        "inject_quarantine_demo",
        "bronze_ingestion",
        "validate_bronze",
        "silver_transformation",
        "validate_silver",
        "wait_for_spark_thrift",
        "dbt_gold_build",
        "validate_gold",
    }
    assert expected_tasks == {task.task_id for task in dag.tasks}

    produce = dag.get_task("produce_events")
    inject = dag.get_task("inject_quarantine_demo")
    bronze = dag.get_task("bronze_ingestion")
    validate_bronze = dag.get_task("validate_bronze")
    silver = dag.get_task("silver_transformation")
    validate_silver = dag.get_task("validate_silver")
    wait = dag.get_task("wait_for_spark_thrift")
    dbt = dag.get_task("dbt_gold_build")
    validate_gold = dag.get_task("validate_gold")

    assert inject in produce.downstream_list
    assert bronze in inject.downstream_list
    assert validate_bronze in bronze.downstream_list
    assert silver in validate_bronze.downstream_list
    assert validate_silver in silver.downstream_list
    assert wait in validate_silver.downstream_list
    assert dbt in wait.downstream_list
    assert validate_gold in dbt.downstream_list


def test_retail_pipeline_retries_configured(dag_bag) -> None:
    dag = dag_bag.get_dag("retail_pipeline")
    assert dag is not None
    assert dag.default_args["retries"] == 2
    assert dag.default_args["retry_delay"] == timedelta(minutes=2)

    for task in dag.tasks:
        assert task.retries == 2


def test_airflow_assets_exist() -> None:
    expected = [
        "airflow/Dockerfile",
        "airflow/requirements.txt",
        "airflow/dags/retail_pipeline_dag.py",
    ]

    missing = [path for path in expected if not (ROOT / path).is_file()]

    assert missing == []


def test_retail_pipeline_dag_source_contract() -> None:
    dag_source = (DAGS_FOLDER / "retail_pipeline_dag.py").read_text()

    for task_id in (
        "produce_events",
        "inject_quarantine_demo",
        "bronze_ingestion",
        "validate_bronze",
        "silver_transformation",
        "validate_silver",
        "wait_for_spark_thrift",
        "dbt_gold_build",
        "validate_gold",
    ):
        assert f'task_id="{task_id}"' in dag_source

    assert '"retries": 2' in dag_source
    assert "timedelta(minutes=2)" in dag_source
    assert "compose_job(" in dag_source
    assert "--build --no-deps" in dag_source
    assert "--abort-on-container-exit" in dag_source
    assert "execution_timeout=JOB_TIMEOUT" in dag_source
    assert "produce_events" in dag_source
    assert ">> inject_quarantine_demo" in dag_source
    assert ">> bronze_ingestion" in dag_source
    assert ">> validate_bronze" in dag_source
    assert ">> silver_transformation" in dag_source
    assert ">> validate_silver" in dag_source
    assert ">> wait_for_spark_thrift" in dag_source
    assert ">> dbt_gold_build" in dag_source
    assert ">> validate_gold" in dag_source
