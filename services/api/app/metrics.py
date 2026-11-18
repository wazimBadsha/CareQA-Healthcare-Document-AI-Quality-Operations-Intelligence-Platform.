"""Pure deterministic metric implementations used by the evaluator."""
from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date
from decimal import Decimal, InvalidOperation


def normalise(value: object, field: str = "") -> object:
    """Normalise only for comparison; callers retain original values."""
    if value is None:
        return None
    if isinstance(value, list):
        return sorted({str(item).strip().casefold() for item in value if str(item).strip()})
    text = str(value).strip()
    if field.endswith("date"):
        # Synthetic generator uses ISO dates; common slash dates are accepted too.
        for candidate in (text, text.replace("/", "-")):
            try:
                return date.fromisoformat(candidate).isoformat()
            except ValueError:
                pass
    if field in {"amount", "dosage_mg"}:
        cleaned = re.sub(r"[^0-9.-]", "", text)
        try:
            return str(Decimal(cleaned).normalize())
        except (InvalidOperation, ValueError):
            return text.casefold()
    return re.sub(r"\s+", " ", text).casefold()


def set_scores(expected: Iterable[object], actual: Iterable[object]) -> dict[str, float]:
    expected_set = set(normalise(list(expected)))
    actual_set = set(normalise(list(actual)))
    hits = len(expected_set & actual_set)
    precision = hits / len(actual_set) if actual_set else (1.0 if not expected_set else 0.0)
    recall = hits / len(expected_set) if expected_set else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def numeric_match(expected: object, actual: object, tolerance: Decimal = Decimal("0")) -> bool:
    try:
        return abs(Decimal(str(expected)) - Decimal(str(actual))) <= tolerance
    except InvalidOperation:
        return False


def evaluate_field(field: str, expected: object, actual: object, required: bool = True) -> tuple[str, dict]:
    """Return a labelled outcome and auditable per-field measurements."""
    complete = actual not in (None, "", [])
    detail: dict[str, object] = {"required": required, "complete": complete}
    if isinstance(expected, list):
        scores = set_scores(expected, actual if isinstance(actual, list) else [])
        detail.update(scores)
        detail["exact_match"] = expected == actual
        detail["normalized_match"] = scores["f1"] == 1.0
        return ("exact_match" if scores["f1"] == 1 else "mismatch"), detail
    exact = expected == actual
    normalised = normalise(expected, field) == normalise(actual, field)
    if field == "dosage_mg" and expected is not None and actual is not None:
        normalised = numeric_match(expected, actual, Decimal("0.5"))
        detail["tolerance"] = "0.5"
    detail.update({"exact_match": exact, "normalized_match": normalised})
    if not complete and required:
        return "missing", detail
    return ("exact_match" if exact else "normalized_match" if normalised else "mismatch"), detail
