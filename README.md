# CareQA

Healthcare Document AI Quality & Operations Intelligence Platform — an independent portfolio engineering project using synthetic healthcare-claim documents only.

CareQA evaluates structured AI extraction against synthetic reference annotations, produces deterministic field-level metrics, and exposes a dashboard. The offline demo requires no API key and does not require a human reviewer to complete a run.

## Current implementation status

- [x] Engineering handoff and architecture baseline — [`docs/ENGINEERING_HANDOFF.md`](docs/ENGINEERING_HANDOFF.md)
- [x] Deterministic synthetic claims benchmark
- [x] Offline mock prediction adapter with controlled injected defects
- [x] Field evaluation and aggregate precision/recall/F1/completeness metrics
- [x] FastAPI health, overview and run endpoints
- [x] Next.js dashboard wired to the API
- [x] Backend tests and GitHub Actions workflow
- [ ] PostgreSQL persistence and migrations
- [ ] Redis/Celery asynchronous processing
- [ ] PDF/OCR and object storage
- [ ] Live LLM provider adapter and model experiment tracking
- [ ] dbt and Power BI export models
- [ ] Full tenant authentication/RLS and production deployment

This is an incremental engineering release, not a claim that the full target architecture is already implemented.

## Quick start

### Backend

```bash
python -m pip install -r services/api/requirements.txt
cd services/api
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for OpenAPI.

### Frontend

In another terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

Set `CAREQA_API_URL=http://localhost:8000` if the API runs elsewhere. For Docker Compose, the frontend uses the internal `http://api:8000` service address.

### Run tests

From repository root:

```bash
python -m pip install -r services/api/requirements.txt
python -m pytest -q
```

### Demo API

```bash
curl http://localhost:8000/api/v1/overview?cases=24\&seed=42
curl -X POST http://localhost:8000/api/v1/runs \\
  -H 'Content-Type: application/json' \\
  -d '{"cases":24,"seed":42}'
```

## Evaluation semantics

- Normalized field matching preserves numeric/string distinction only through canonical string normalisation; domain-specific rules should be added for production field types.
- Completeness is based on required reference fields populated by prediction.
- Precision, recall and F1 are aggregated over comparable reference/predicted fields.
- Mock predictions deliberately inject a deterministic proportion of defects to demonstrate metric behaviour. These metrics are not model performance claims.

## Safety boundary

Use only synthetic or explicitly approved public non-sensitive data. Do not upload patient records or former-employer data. CareQA is not a clinical product and makes no healthcare regulatory compliance claim.
