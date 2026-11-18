"""Regression coverage for the deterministic evaluator contract."""
from decimal import Decimal

from app.metrics import evaluate_field, normalise, numeric_match, set_scores
from app.synthetic import generate_cases


def test_text_and_date_normalisation():
    assert normalise("  Al Noor   Clinic ") == normalise("al noor clinic")
    assert normalise("2026/02/03", "encounter_date") == "2026-02-03"


def test_numeric_tolerance_does_not_coerce_invalid_values():
    assert numeric_match("10.0", "10.04", Decimal("0.05"))
    assert not numeric_match("10.0", "invalid", Decimal("0.05"))


def test_field_results_and_entity_f1_are_reproducible():
    outcome, detail = evaluate_field("diagnosis", "asthma", "ASTHMA")
    assert outcome == "normalized_match"
    assert detail["normalized_match"] is True
    assert set_scores(["A", "B"], ["a", "B"])["f1"] == 1
    assert generate_cases(2, 11) == generate_cases(2, 11)
