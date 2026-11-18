# Implementation status

This repository currently contains the first executable offline vertical slice. The engineering handoff defines the target architecture; this file distinguishes delivered capability from planned work.

## Delivered
- Deterministic synthetic claims benchmark generation.
- Offline mock model adapter with reproducible injected defects.
- Deterministic field evaluation and aggregate metrics.
- FastAPI live/ready endpoints, overview and run API.
- Next.js dashboard rendering API-backed KPI values.
- Backend unit/API tests and GitHub Actions CI.

## Not yet delivered
- PostgreSQL persistence, Alembic migrations, tenant authentication/RLS.
- Durable Redis/Celery queue and transactional outbox.
- File upload pipeline, PyMuPDF/Tesseract, MinIO/S3.
- Live provider integration, summary LLM judge, MLflow.
- dbt project and Power BI report.
- OpenTelemetry/Prometheus/Grafana integration.
- Full frontend component/e2e suite, deployment and security audit.

## Known metric interpretation
The first release uses deterministic synthetic data and an offline adapter. Its scores validate the evaluator implementation and dashboard wiring only. They must not be represented as healthcare model quality or operational outcomes.
