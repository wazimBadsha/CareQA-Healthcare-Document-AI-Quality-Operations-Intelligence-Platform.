"""Offline adapter and deterministic evaluation application service."""
from __future__ import annotations

import hashlib
import platform
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .metrics import evaluate_field
from .models import AuditEvent, Dataset, DatasetCase, EvaluationRun, FieldResult, Prediction, RunMetric

EVALUATOR_VERSION = "deterministic-fields-v1"


class OfflineAdapter:
    """A reproducible, intentionally imperfect adapter for no-key demos."""

    name = "deterministic-baseline"

    def predict(self, reference: dict, seed: int, case_key: str) -> tuple[dict, int]:
        output = dict(reference)
        selector = int(hashlib.sha256(f"{seed}:{case_key}".encode()).hexdigest()[:8], 16) % 7
        # Inject one predictable defect periodically to exercise defect analytics.
        if selector == 0:
            output["facility"] = "Unknown facility"
        elif selector == 1:
            output["dosage_mg"] = reference["dosage_mg"] + 5
        elif selector == 2:
            output["conditions"] = reference["conditions"][:1]
        elif selector == 3:
            output["follow_up_days"] = None
        latency = 20 + int(hashlib.sha256(case_key.encode()).hexdigest()[:2], 16) % 45
        return output, latency


def _aggregate(field_results: list[FieldResult], predictions: list[Prediction]) -> dict[str, float]:
    count = len(field_results)
    required = [result for result in field_results if result.metric_json.get("required")]
    exact = sum(result.metric_json.get("exact_match", False) for result in field_results)
    normalized = sum(result.metric_json.get("normalized_match", False) for result in field_results)
    complete = sum(result.metric_json.get("complete", False) for result in required)
    set_details = [result.metric_json for result in field_results if "f1" in result.metric_json]
    invalid_schema_prediction_ids = {result.prediction_id for result in field_results if result.outcome == "missing"}
    metrics = {
        "field_exact_accuracy": exact / count if count else 0.0,
        "field_normalized_accuracy": normalized / count if count else 0.0,
        "completeness": complete / len(required) if required else 1.0,
        "defect_count": float(sum(result.outcome in {"mismatch", "missing"} for result in field_results)),
        "schema_validity": (len(predictions) - len(invalid_schema_prediction_ids)) / len(predictions) if predictions else 1.0,
        "average_latency_ms": sum(pred.latency_ms for pred in predictions) / len(predictions) if predictions else 0.0,
    }
    for key in ("precision", "recall", "f1"):
        metrics[f"entity_{key}"] = sum(float(item[key]) for item in set_details) / len(set_details) if set_details else 1.0
    return metrics


def execute_run(db: Session, run: EvaluationRun) -> EvaluationRun:
    """Execute synchronously behind a worker-ready service boundary."""
    dataset = db.scalar(select(Dataset).where(Dataset.id == run.dataset_id, Dataset.tenant_id == run.tenant_id))
    if not dataset:
        raise ValueError("dataset is outside the tenant scope")
    cases = list(db.scalars(select(DatasetCase).where(DatasetCase.dataset_id == dataset.id).order_by(DatasetCase.case_key)))
    if not cases:
        raise ValueError("dataset has no cases")
    run.status = "running"
    run.started_at = datetime.now(UTC)
    db.flush()
    adapter = OfflineAdapter()
    predictions: list[Prediction] = []
    field_results: list[FieldResult] = []
    try:
        for case in cases:
            output, latency_ms = adapter.predict(case.reference_json, run.random_seed, case.case_key)
            prediction = Prediction(
                run_id=run.id,
                case_id=case.id,
                output_json=output,
                summary_text=f"Synthetic offline extraction for {case.case_key}.",
                latency_ms=latency_ms,
                token_usage_json={"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0},
            )
            db.add(prediction)
            db.flush()
            predictions.append(prediction)
            for field, expected in case.reference_json.items():
                outcome, detail = evaluate_field(field, expected, output.get(field), required=True)
                result = FieldResult(
                    prediction_id=prediction.id,
                    field_path=field,
                    expected_value=expected,
                    actual_value=output.get(field),
                    outcome=outcome,
                    metric_json=detail,
                )
                db.add(result)
                field_results.append(result)
        db.flush()
        units = {"defect_count": "count", "average_latency_ms": "ms"}
        for name, value in _aggregate(field_results, predictions).items():
            db.add(RunMetric(run_id=run.id, metric_name=name, metric_value=value, metric_unit=units.get(name, "ratio")))
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        db.add(AuditEvent(tenant_id=run.tenant_id, action="run.completed", resource_type="evaluation_run", resource_id=run.id,
                          metadata_json={"case_count": len(cases), "adapter": adapter.name}))
        db.commit()
    except Exception as exc:
        db.rollback()
        run = db.get(EvaluationRun, run.id)
        run.status = "failed"
        run.failure_reason = type(exc).__name__
        run.completed_at = datetime.now(UTC)
        db.commit()
        raise
    return run


def run_metadata(seed: int) -> dict:
    return {"runtime": "python", "python": platform.python_version(), "platform": platform.system(), "seed": seed}
