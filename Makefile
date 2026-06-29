.PHONY: up down ps logs config lint test produce dry-run

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
	python -m compileall producer consumer spark fastapi streamlit ml tests

test:
	python -m pytest

dry-run:
	python -m producer.main --events 2 --rate 0 --dry-run

produce:
	python -m producer.main --bootstrap-server localhost:29092 --events 100 --rate 25
