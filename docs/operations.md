# Operations guide

## Local development

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Browse `http://localhost:3000`; API documentation is at `http://localhost:8000/docs`.
4. Use `docker compose exec api python -m app.cli demo --cases 40 --seed 2026` for a new benchmark and persisted run.

The API initialises the schema and seeds exactly one synthetic dataset on first boot. For production-like lifecycle management, run Alembic migrations (`alembic upgrade head`) before starting the service and remove `create_all` from the startup path in a deployment-specific configuration.

## Health and recovery

- `/health/live` confirms the process can serve requests.
- `/health/ready` performs a lightweight database query.
- A failed run persists `status=failed` and a failure class, without storing exception contents.
- All demo data is synthetic. Deleting the Docker volume clears local runs and benchmark data.

## Current security boundary

The text ingestion route exists solely for synthetic/demo text and stores a hash. It is not a binary upload pipeline. Before accepting user files, add MIME and magic-byte checks, page/size limits, server-side object names, malware scanning, signed short-lived access, retention/deletion controls, rate limits, real authentication, secret management, and a formal privacy/regulatory review.


