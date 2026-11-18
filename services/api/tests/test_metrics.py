from decimal import Decimal

from app.metrics import evaluate_field, normalise, numeric_match, set_scores
from app.synthetic import generate_cases


def test_normalisation_preserves_comparison_rules():
    assert normalise("  AL Noor   Clinic ") == normalise("al noor clinic")
    assert normalise("2026/03/05", "encounter_date") == "2026-03-05"
    assert normalise("AED 10.00", "dosage_mg") == "1E+1"


def test_numeric_tolerance_and_entity_metrics():
    assert numeric_match("10.00", "10.04", Decimal("0.05"))
    assert not numeric_match("10.00", "10.10", Decimal("0.05"))
    scores = set_scores(["A", "B"], ["a", "C"])
    assert scores == {"precision": 0.5, "recall": 0.5, "f1": 0.5}


def test_missing_and_array_fields_are_auditable():
    outcome, detail = evaluate_field("diagnosis", "asthma", None)
    assert outcome == "missing" and detail["complete"] is False
    outcome, detail = evaluate_field("conditions", ["one", "two"], ["TWO", "one"])
    assert outcome == "exact_match" and detail["f1"] == 1


def test_synthetic_generation_is_deterministic():
    assert generate_cases(3, 7) == generate_cases(3, 7)
