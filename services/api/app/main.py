from __future__ import annotations

import hashlib
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, engine, get_db
from .evaluator import execute_run, run_metadata
from .models import (
    AuditEvent,
    Dataset,
    DatasetCase,
    Document,
    EvaluationRun,
    FieldResult,
    Prediction,
    RunMetric,
    Tenant,
)
from .schemas import (
    CaseCreate,
    DatasetCreate,
    DatasetOut,
    DemoDatasetCreate,
    DocumentCreate,
    MetricOut,
    RunCreate,
    RunOut,
)
from .seed import create_synthetic_dataset, seed_demo


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with next(get_db()) as db:
        seed_demo(db)
    yield


app = FastAPI(title="CareQA API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.headers.get(
        "X-Request-ID", hashlib.sha256(str(datetime.now(UTC)).encode()).hexdigest()[:16]
    )
    return response


@app.exception_handler(HTTPException)
async def error_envelope(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": str(exc.status_code), "message": str(exc.detail)}},
    )


def tenant_scope(
    x_tenant_id: str = Header(default="demo", alias="X-Tenant-Id"),
    db: Session = Depends(get_db),
) -> Tenant:
    tenant = db.scalar(select(Tenant).where(Tenant.slug == x_tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="tenant not found")
    if tenant.status != "active":
        raise HTTPException(status_code=403, detail="tenant is inactive")
    return tenant


def dataset_out(dataset: Dataset) -> DatasetOut:
    return DatasetOut(
        id=dataset.id,
        name=dataset.name,
        version=dataset.version,
        content_hash=dataset.content_hash,
        case_count=len(dataset.cases),
        created_at=dataset.created_at,
    )


def run_out(run: EvaluationRun) -> RunOut:
    return RunOut(
        id=run.id,
        dataset_id=run.dataset_id,
        status=run.status,
        prompt_version=run.prompt_version,
        evaluator_version=run.evaluator_version,
        random_seed=run.random_seed,
        started_at=run.started_at,
        completed_at=run.completed_at,
        failure_reason=run.failure_reason,
    )


@app.get("/health/live")
def live() -> dict:
    return {"status": "ok"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    db.execute(select(1))
    return {"status": "ready"}


@app.get("/api/v1/overview")
def overview(
    tenant: Tenant = Depends(tenant_scope), db: Session = Depends(get_db)
) -> dict:
    runs = list(
        db.scalars(
            select(EvaluationRun)
            .where(EvaluationRun.tenant_id == tenant.id)
            .order_by(EvaluationRun.created_at.desc())
        )
    )
    completed = [run for run in runs if run.status == "completed"]
    latest = completed[0] if completed else None
    metrics = (
        list(db.scalars(select(RunMetric).where(RunMetric.run_id == latest.id)))
        if latest
        else []
    )
    metric_map = {metric.metric_name: metric.metric_value for metric in metrics}
    return {
        "tenant": {"id": tenant.id, "slug": tenant.slug, "name": tenant.name},
        "run_count": len(runs),
        "completed_run_count": len(completed),
        "latest_run_id": latest.id if latest else None,
        "metrics": metric_map,
        "status_counts": {
            state: sum(run.status == state for run in runs)
            for state in ("queued", "running", "completed", "failed")
        },
    }


@app.get("/api/v1/datasets", response_model=list[DatasetOut])
def list_datasets(
    tenant: Tenant = Depends(tenant_scope), db: Session = Depends(get_db)
) -> list[DatasetOut]:
    datasets = list(
        db.scalars(
            select(Dataset)
            .where(Dataset.tenant_id == tenant.id)
            .order_by(Dataset.created_at.desc())
        )
    )
    return [dataset_out(dataset) for dataset in datasets]


@app.post(
    "/api/v1/datasets", response_model=DatasetOut, status_code=status.HTTP_201_CREATED
)
def create_dataset(
    payload: DatasetCreate,
    tenant: Tenant = Depends(tenant_scope),
    db: Session = Depends(get_db),
) -> DatasetOut:
    dataset = Dataset(
        tenant_id=tenant.id,
        name=payload.name,
        version=payload.version,
        content_hash=hashlib.sha256(b"[]").hexdigest(),
        schema_json=payload.schema_definition,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset_out(dataset)


@app.post(
    "/api/v1/datasets/demo",
    response_model=DatasetOut,
    status_code=status.HTTP_201_CREATED,
)
def create_demo_dataset(
    payload: DemoDatasetCreate,
    tenant: Tenant = Depends(tenant_scope),
    db: Session = Depends(get_db),
) -> DatasetOut:
    try:
        dataset = create_synthetic_dataset(
            db, tenant, payload.name, payload.version, payload.cases, payload.seed
        )
    except Exception as exc:
        raise HTTPException(
            status_code=409, detail=f"cannot create benchmark: {type(exc).__name__}"
        ) from exc
    return dataset_out(dataset)


@app.post("/api/v1/datasets/{dataset_id}/cases", status_code=status.HTTP_201_CREATED)
def add_case(
    dataset_id: str,
    payload: CaseCreate,
    tenant: Tenant = Depends(tenant_scope),
    db: Session = Depends(get_db),
) -> dict:
    dataset = db.scalar(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.tenant_id == tenant.id)
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="dataset not found")
    case = DatasetCase(dataset_id=dataset.id, **payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return {"id": case.id, "case_key": case.case_key}


@app.get("/api/v1/documents")
def list_documents(
    tenant: Tenant = Depends(tenant_scope), db: Session = Depends(get_db)
) -> list[dict]:
    docs = db.scalars(
        select(Document)
        .where(Document.tenant_id == tenant.id)
        .order_by(Document.created_at.desc())
    ).all()
    return [
        {
            "id": doc.id,
            "status": doc.status,
            "storage_key": doc.storage_key,
            "sha256": doc.sha256,
            "created_at": doc.created_at,
        }
        for doc in docs
    ]


@app.post("/api/v1/documents", status_code=status.HTTP_201_CREATED)
def ingest_document(
    payload: DocumentCreate,
    tenant: Tenant = Depends(tenant_scope),
    db: Session = Depends(get_db),
) -> dict:
    """Persist text supplied by the synthetic/demo ingestion path.

    Binary upload, PDF parsing and malware scanning are intentionally extension work;
    this endpoint does not claim to accept clinical files.
    """
    if payload.dataset_case_id:
        case = db.scalar(
            select(DatasetCase)
            .join(Dataset)
            .where(
                DatasetCase.id == payload.dataset_case_id,
                Dataset.tenant_id == tenant.id,
            )
        )
        if not case:
            raise HTTPException(status_code=404, detail="dataset case not found")
    document = Document(
        tenant_id=tenant.id,
        dataset_case_id=payload.dataset_case_id,
        storage_key=payload.storage_key,
        sha256=hashlib.sha256(payload.extracted_text.encode()).hexdigest(),
        extracted_text=payload.extracted_text,
    )
    db.add(document)
    db.flush()
    db.add(
        AuditEvent(
            tenant_id=tenant.id,
            action="document.ingested",
            resource_type="document",
            resource_id=document.id,
            metadata_json={"sha256": document.sha256, "mode": "synthetic-text"},
        )
    )
    db.commit()
    db.refresh(document)
    return {"id": document.id, "status": document.status, "sha256": document.sha256}


@app.get("/api/v1/documents/{document_id}")
def get_document(
    document_id: str,
    tenant: Tenant = Depends(tenant_scope),
    db: Session = Depends(get_db),
) -> dict:
    document = db.scalar(
        select(Document).where(
            Document.id == document_id, Document.tenant_id == tenant.id
        )
    )
    if not document:
        raise HTTPException(status_code=404, detail="document not found")
    return {
        "id": document.id,
        "status": document.status,
        "storage_key": document.storage_key,
        "sha256": document.sha256,
        "dataset_case_id": document.dataset_case_id,
        "extracted_text": document.extracted_text,
        "created_at": document.created_at,
    }


@app.get("/api/v1/runs", response_model=list[RunOut])
def list_runs(
    tenant: Tenant = Depends(tenant_scope), db: Session = Depends(get_db)
) -> list[RunOut]:
    return [
        run_out(run)
        for run in db.scalars(
            select(EvaluationRun)
            .where(EvaluationRun.tenant_id == tenant.id)
            .order_by(EvaluationRun.created_at.desc())
        )
    ]


@app.post("/api/v1/runs", response_model=RunOut, status_code=status.HTTP_201_CREATED)
def create_run(
    payload: RunCreate,
    tenant: Tenant = Depends(tenant_scope),
    db: Session = Depends(get_db),
) -> RunOut:
    dataset = db.scalar(
        select(Dataset).where(
            Dataset.id == payload.dataset_id, Dataset.tenant_id == tenant.id
        )
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="dataset not found")
    if payload.evaluator_version != "deterministic-fields-v1":
        raise HTTPException(status_code=422, detail="unsupported evaluator version")
    run = EvaluationRun(
        tenant_id=tenant.id,
        dataset_id=dataset.id,
        prompt_version=payload.prompt_version,
        prompt_hash=hashlib.sha256(payload.prompt_version.encode()).hexdigest(),
        evaluator_version=payload.evaluator_version,
        random_seed=payload.seed,
        environment_json=run_metadata(payload.seed),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    execute_run(db, run)
    return run_out(run)


@app.get("/api/v1/runs/{run_id}", response_model=RunOut)
def get_run(
    run_id: str, tenant: Tenant = Depends(tenant_scope), db: Session = Depends(get_db)
) -> RunOut:
    run = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.id == run_id, EvaluationRun.tenant_id == tenant.id
        )
    )
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run_out(run)


@app.get("/api/v1/runs/{run_id}/metrics", response_model=list[MetricOut])
def run_metrics(
    run_id: str, tenant: Tenant = Depends(tenant_scope), db: Session = Depends(get_db)
) -> list[MetricOut]:
    run = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.id == run_id, EvaluationRun.tenant_id == tenant.id
        )
    )
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return [
        MetricOut(
            metric_name=m.metric_name,
            metric_value=m.metric_value,
            metric_unit=m.metric_unit,
        )
        for m in db.scalars(
            select(RunMetric)
            .where(RunMetric.run_id == run.id)
            .order_by(RunMetric.metric_name)
        )
    ]


@app.get("/api/v1/runs/{run_id}/results")
def run_results(
    run_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    tenant: Tenant = Depends(tenant_scope),
    db: Session = Depends(get_db),
) -> dict:
    run = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.id == run_id, EvaluationRun.tenant_id == tenant.id
        )
    )
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    rows = db.execute(
        select(FieldResult, Prediction, DatasetCase)
        .join(Prediction, FieldResult.prediction_id == Prediction.id)
        .join(DatasetCase, Prediction.case_id == DatasetCase.id)
        .where(Prediction.run_id == run.id)
        .order_by(DatasetCase.case_key, FieldResult.field_path)
        .limit(limit)
    ).all()
    return {
        "run_id": run.id,
        "items": [
            {
                "case_key": case.case_key,
                "field_path": field.field_path,
                "expected": field.expected_value,
                "actual": field.actual_value,
                "outcome": field.outcome,
                "metrics": field.metric_json,
                "latency_ms": prediction.latency_ms,
            }
            for field, prediction, case in rows
        ],
    }


@app.get("/api/v1/compare")
def compare(
    baseline: str,
    candidate: str,
    tenant: Tenant = Depends(tenant_scope),
    db: Session = Depends(get_db),
) -> dict:
    runs = list(
        db.scalars(
            select(EvaluationRun).where(
                EvaluationRun.id.in_([baseline, candidate]),
                EvaluationRun.tenant_id == tenant.id,
            )
        )
    )
    if len(runs) != 2:
        raise HTTPException(status_code=404, detail="one or both runs not found")
    baseline_run = next(run for run in runs if run.id == baseline)
    candidate_run = next(run for run in runs if run.id == candidate)
    if (
        baseline_run.dataset_id != candidate_run.dataset_id
        or baseline_run.evaluator_version != candidate_run.evaluator_version
    ):
        raise HTTPException(
            status_code=422,
            detail="runs are not comparable: dataset and evaluator must match",
        )
    metrics = list(
        db.scalars(select(RunMetric).where(RunMetric.run_id.in_([baseline, candidate])))
    )
    grouped: dict[str, dict[str, float]] = {}
    for metric in metrics:
        grouped.setdefault(metric.metric_name, {})[metric.run_id] = metric.metric_value
    return {
        "baseline": baseline,
        "candidate": candidate,
        "deltas": [
            {
                "metric_name": name,
                "baseline": values.get(baseline, 0),
                "candidate": values.get(candidate, 0),
                "delta": values.get(candidate, 0) - values.get(baseline, 0),
            }
            for name, values in sorted(grouped.items())
        ],
    }


@app.get("/api/v1/audit/events")
def audit_events(
    tenant: Tenant = Depends(tenant_scope), db: Session = Depends(get_db)
) -> list[dict]:
    return [
        {
            "action": event.action,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "metadata": event.metadata_json,
            "created_at": event.created_at,
        }
        for event in db.scalars(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant.id)
            .order_by(AuditEvent.created_at.desc())
            .limit(100)
        )
    ]
