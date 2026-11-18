.DEFAULT_GOAL := help

.PHONY: help up down logs test api-test web-build demo

help:
	@echo "Targets: up down logs test api-test web-build demo"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test: api-test web-build

api-test:
	docker compose run --rm api pytest

web-build:
	docker compose run --rm web npm run build

demo:
	docker compose exec api python -m app.cli demo --cases 40 --seed 2026


