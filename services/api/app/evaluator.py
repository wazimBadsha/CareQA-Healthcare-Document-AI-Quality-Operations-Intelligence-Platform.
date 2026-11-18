"""Deterministic, explainable evaluation primitives for CareQA."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Iterable


def normalize(value: Any, *, casefold: bool = True) -> str:
    """Normalize scalar values conservatively; never coerce unlike values."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float, Decimal)):
        try:
            number = Decimal(str(value)).normalize()
            return format(number, "f")
        except InvalidOperation:
            return str(value).strip()
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text.casefold() if casefold else text


def compare_values(expected: Any, actual: Any, *, mode: str = "normalized", tolerance: Decimal | None = None) -> bool:
    if mode == "exact":
        return type(expected) is type(actual) and expected == actual
    if mode not in {"normalized", "numeric_tolerance"}:
        raise ValueError(f"Unsupported comparison mode: {mode}")
    if mode == "numeric_tolerance":
        if tolerance is None or tolerance < 0:
            raise ValueError("A non-negative tolerance is required")
        try:
            return abs(Decimal(str(expected)) - Decimal(str(actual))) <= tolerance
        except (InvalidOperation, TypeError, ValueError):
            return False
    return normalize(expected) == normalize(actual)


@dataclass(frozen=True)
class FieldEvaluation:
    field: str
    expected: Any
    actual: Any
    matched: bool
    required: bool


def evaluate_fields(reference: dict[str, Any], prediction: dict[str, Any], required_fields: Iterable[str] | None = None) -> dict[str, Any]:
    """Evaluate a flat object. Missing predictions are false, not silently ignored."""
    required = set(required_fields if required_fields is not None else reference.keys())
    fields = sorted(set(reference) | set(prediction) | required)
    results: list[FieldEvaluation] = []
    for name in fields:
        expected = reference.get(name)
        actual = prediction.get(name)
        matched = name in reference and name in prediction and compare_values(expected, actual)
        results.append(FieldEvaluation(name, expected, actual, matched, name in required))
    required_total = len(required)
    required_present = sum(1 for f in results if f.required and f.actual not in (None, ""))
    required_correct = sum(1 for f in results if f.required and f.matched)
    tp = sum(1 for f in results if f.matched and f.expected not in (None, ""))
    fp = sum(1 for f in results if f.actual not in (None, "") and (f.field not in reference or not f.matched))
    fn = sum(1 for f in results if f.expected not in (None, "") and (f.field not in prediction or not f.matched))
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    compared = len(results)
    correct = sum(1 for f in results if f.matched)
    return {
        "field_results": [
            {"field": f.field, "expected": f.expected, "actual": f.actual, "matched": f.matched, "required": f.required}
            for f in results
        ],
        "exact_or_normalized_accuracy": correct / compared if compared else 1.0,
        "completeness": required_present / required_total if required_total else 1.0,
        "required_field_accuracy": required_correct / required_total if required_total else 1.0,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "counts": {"fields_compared": compared, "correct": correct, "true_positive": tp, "false_positive": fp, "false_negative": fn, "required": required_total, "required_present": required_present},
    }


def evaluate_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    reference = case["reference"]
    required = case.get("required_fields", list(reference.keys()))
    metrics = evaluate_fields(reference, prediction, required)
    return {"case_id": case["case_id"], "document_type": case["document_type"], "prediction": prediction, **metrics}


def aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {"case_count": 0, "field_accuracy": 1.0, "completeness": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0, "defect_count": 0}
    totals = {key: sum(r["counts"][key] for r in results) for key in ("fields_compared", "correct", "true_positive", "false_positive", "false_negative", "required", "required_present")}
    tp, fp, fn = totals["true_positive"], totals["false_positive"], totals["false_negative"]
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    return {
        "case_count": len(results),
        "field_accuracy": totals["correct"] / totals["fields_compared"] if totals["fields_compared"] else 1.0,
        "completeness": totals["required_present"] / totals["required"] if totals["required"] else 1.0,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "defect_count": totals["false_positive"] + totals["false_negative"],
        "counts": totals,
    }
