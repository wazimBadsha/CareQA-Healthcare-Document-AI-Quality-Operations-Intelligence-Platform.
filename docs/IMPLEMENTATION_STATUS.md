# Implementation status

This repository implements a persisted, deterministic P0 vertical slice. The engineering handoff remains the architecture target; this document distinguishes working code from planned extensions.

## Delivered

- Deterministic synthetic benchmark generation with a stable seed and content hash.
- Tenant-scoped SQLite/PostgreSQL-ready persistence for datasets, cases, documents, model configuration, runs, predictions, field outcomes, aggregate metrics, and audit metadata.
- Alembic initial schema migration and Docker Compose PostgreSQL service.
- Offline adapter with controlled reproducible defects, field exact/normalized checks, completeness, numeric tolerance, and set precision/recall/F1.
- Synchronous worker-ready run service, reproducibility metadata, run lifecycle persistence, results/metrics APIs, and same-dataset comparison.
- API-backed dashboard with loading/error status, live overview, benchmark trigger, run history, and field-level outcome inspection.
- Backend test coverage for metrics, persistence path, tenant denial, and comparison; CI runs Ruff, pytest, frontend type checking/build, and secret scanning.

## Planned / not claimed

- Real identity authentication, RBAC, PostgreSQL row-level security, rate limiting, and production secrets management.
- Binary upload validation, PDF/OCR, malware scanning, object storage, signed URLs, retention/deletion workflows.
- Redis/Celery/outbox, retry/idempotency worker execution, live LLM provider adapters, summary judge signals, and MLflow.
- dbt/Power BI export models, OpenTelemetry/Prometheus/Grafana, frontend component tests, and Playwright end-to-end coverage.

## Metric interpretation

Scores are generated only from synthetic fixtures and a deterministic mock adapter. They validate implementation behavior and must not be represented as healthcare model performance, clinical quality, or operational production outcomes.


