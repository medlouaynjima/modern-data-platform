|.PHONY: up down ps logs config lint test produce dry-run bronze silver gold dbt-debug airflow pipeline validate-bronze validate-silver validate-gold validate-silver validate-gold

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=100

config:
	docker compose config

lint:
	python -m compileall producer consumer spark contracts data_quality fastapi streamlit ml tests

test:
	python -m pytest

dry-run:
	python -m producer.main --events 2 --rate 0 --dry-run

produce:
	python -m producer.main --bootstrap-server localhost:29092 --events 100 --rate 25

bronze:
	docker compose --profile spark up spark-bronze

silver:
	docker compose --profile spark up spark-silver

gold:
	docker compose --profile dbt up --build dbt

dbt-debug:
	docker compose --profile dbt run --rm dbt debug --profiles-dir /usr/app/dbt --project-dir /usr/app/dbt

airflow:
	docker compose --profile airflow up -d --build

pipeline:
	docker compose --profile airflow exec airflow-scheduler airflow dags trigger retail_pipeline

validate-bronze:
	docker compose --profile ge up --build ge-bronze

validate-silver:
	docker compose --profile ge up --build ge-silver

validate-gold:
	docker compose --profile ge up --build ge-gold
