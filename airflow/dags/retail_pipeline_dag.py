"""Retail lakehouse pipeline orchestration."""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"
COMPOSE = f"docker-compose --project-directory {PROJECT_DIR}"
JOB_TIMEOUT = timedelta(minutes=30)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def compose_job(profile: str, service: str) -> str:
    return (
        f"{COMPOSE} --profile {profile} up --no-deps "
        f"--abort-on-container-exit --remove-orphans {service}"
    )


with DAG(
    dag_id="retail_pipeline",
    description="Produce retail events, ingest Bronze, transform Silver, and build Gold dbt marts.",
    default_args=DEFAULT_ARGS,
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["mdp", "retail", "lakehouse"],
) as dag:
    produce_events = BashOperator(
        task_id="produce_events",
        bash_command=compose_job("producers", "producer"),
        execution_timeout=timedelta(minutes=10),
    )

    bronze_ingestion = BashOperator(
        task_id="bronze_ingestion",
        bash_command=compose_job("spark", "spark-bronze"),
        execution_timeout=JOB_TIMEOUT,
    )

    silver_transformation = BashOperator(
        task_id="silver_transformation",
        bash_command=compose_job("spark", "spark-silver"),
        execution_timeout=JOB_TIMEOUT,
    )

    wait_for_spark_thrift = BashOperator(
        task_id="wait_for_spark_thrift",
        bash_command="bash -c 'until </dev/tcp/spark-thrift/10000; do sleep 5; done'",
        execution_timeout=timedelta(minutes=5),
    )

    dbt_gold_build = BashOperator(
        task_id="dbt_gold_build",
        bash_command=compose_job("dbt", "dbt"),
        execution_timeout=JOB_TIMEOUT,
    )

    (
        produce_events
        >> bronze_ingestion
        >> silver_transformation
        >> wait_for_spark_thrift
        >> dbt_gold_build
    )
