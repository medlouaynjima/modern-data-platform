.PHONY: up down ps logs config lint test

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
