# CareQA

CareQA is an independent portfolio application for evaluating AI-assisted extraction from **synthetic healthcare documents**. It is not a medical device, clinical decision-support system, or compliance-certified platform.

The executable vertical slice is deliberately offline-first: deterministic synthetic fixtures flow through a mock extraction adapter, grounded field-level evaluation, persistent run records, comparison analytics, and a Next.js dashboard. No API key or patient data is needed.

## What is implemented

- FastAPI API, versioned under `/api/v1`, with OpenAPI documentation at `/docs`
- Postgres-ready SQLAlchemy persistence and an SQLite test/local fallback
- Tenant-scoped datasets, cases, documents, runs, predictions, field results, metrics, and audit records
- Deterministic benchmark generator, offline adapter, reproducible run metadata, and defect injection
- Exact/normalised match, completeness, set precision/recall/F1, numeric tolerance, and schema-validity metrics
- Next.js dashboard for overview, runs, drill-down results, and compatible-run comparison
- Docker Compose development environment, tests, CI, architecture and operations docs

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:3000`. The API seeds a demo tenant and dataset on first boot. To create and evaluate a new deterministic benchmark:

```bash
docker compose exec api python -m app.cli demo --cases 40 --seed 2026
```

The command prints the run ID; use it in the dashboard or API. To run API tests locally:

```bash
cd services/api
python -m pip install -r requirements-dev.txt
pytest
```

## API examples

```bash
curl http://localhost:8000/health/ready
curl http://localhost:8000/api/v1/overview
curl -X POST http://localhost:8000/api/v1/runs \
  -H 'Content-Type: application/json' \
  -d '{"dataset_id":"<dataset UUID>","prompt_version":"baseline-v1"}'
```

All protected-domain endpoints accept `X-Tenant-Id`; the default is the seeded `demo` tenant. This is a development tenant boundary, not production authentication.

## Important limitations

- The initial release has a synchronous, deterministic offline execution path. Redis/Celery, live provider adapters, OCR/PDF processing, object storage, MLflow, dbt and operational telemetry are planned extension points, not implemented claims.
- The supplied mock prediction is intentionally imperfect so the dashboard exposes detected defects. It must not be interpreted as a real clinical-model benchmark.
- The project contains synthetic data only. Never upload identifiable patient data, credentials, or confidential records.
- Use a proper identity provider, tenant RLS, signed artifact access, rate limiting, malware scanning, secrets management, and a formal regulatory review before any production use.

Further details: [architecture](docs/architecture.md), [metric contract](docs/metrics.md), [operations](docs/operations.md), and [security boundary](docs/security.md).
