# 01 — Backend quality gate

## Environment

- Python `3.12.10`
- FastAPI `0.115.6`
- SQLAlchemy `2.0.36`
- SQLite test database

## Commands and result

```text
ruff check app tests
All checks passed!

python -m pytest -q
11 passed, 1 warning in 2.36s
```

The warning originates in Starlette's TestClient dependency and does not affect an application assertion.

## Coverage of this run

- deterministic normalisation, tolerance, completeness, and entity F1
- seeded tenant/dataset API path
- persisted run metrics and field-level results
- compatible-run comparison
- tenant-denial behavior
- document ingestion plus audit persistence

During this validation, an ingestion audit-event ordering defect was found and corrected before the final passing run: the document is now flushed before its audit event references the document ID.
