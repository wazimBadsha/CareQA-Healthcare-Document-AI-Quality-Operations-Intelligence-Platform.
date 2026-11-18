.PHONY: api-install test api web-install web-dev demo compose-up compose-down
api-install:
	python -m pip install -r services/api/requirements.txt
test:
	python -m pytest -q
api:
	cd services/api && uvicorn app.main:app --reload
web-install:
	cd apps/web && npm install
web-dev:
	cd apps/web && npm run dev
demo:
	cd services/api && python -c 'from app.demo import run_demo; import json; print(json.dumps(run_demo(), indent=2))'
compose-up:
	docker compose up --build
compose-down:
	docker compose down
