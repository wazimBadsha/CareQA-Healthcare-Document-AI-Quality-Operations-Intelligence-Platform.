"""CareQA HTTP API. The offline benchmark works without external credentials."""
from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .demo import run_demo

app = FastAPI(title="CareQA API", version="0.1.0", description="Synthetic healthcare document AI quality evaluation")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["*"])

@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}

@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "mode": "offline-demo"}

@app.get("/api/v1/overview")
def overview(cases: int = Query(default=24, ge=1, le=10000), seed: int = Query(default=42, ge=0)) -> dict:
    report = run_demo(count=cases, seed=seed)
    return {"dataset": report["dataset"], "model": report["model"], "metrics": report["metrics"]}

@app.post("/api/v1/runs")
def create_run(payload: dict | None = None) -> dict:
    payload = payload or {}
    try:
        count = int(payload.get("cases", 24))
        seed = int(payload.get("seed", 42))
        report = run_demo(count=count, seed=seed)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "completed", "run_id": f"offline-{seed}-{count}", **report}

@app.get("/api/v1/runs/{run_id}")
def get_run(run_id: str, cases: int = Query(default=24, ge=1, le=10000), seed: int = Query(default=42, ge=0)) -> dict:
    expected = f"offline-{seed}-{cases}"
    if run_id != expected:
        raise HTTPException(status_code=404, detail="Run not found. Offline runs are reproducibly derived from seed and case count.")
    return create_run({"cases": cases, "seed": seed})
