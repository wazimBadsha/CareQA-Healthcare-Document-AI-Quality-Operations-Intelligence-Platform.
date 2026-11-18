from app.evaluator import aggregate_results, compare_values, evaluate_fields
from app.demo import generate_cases, offline_predict


def test_normalized_match():
    assert compare_values("  AL Noor   Clinic ", "al noor clinic")


def test_numeric_tolerance():
    from decimal import Decimal
    assert compare_values("10.00", "10.04", mode="numeric_tolerance", tolerance=Decimal("0.05"))
    assert not compare_values("10.00", "10.10", mode="numeric_tolerance", tolerance=Decimal("0.05"))


def test_missing_required_field_reduces_completeness():
    result = evaluate_fields({"a": "x", "b": "y"}, {"a": "x"}, ["a", "b"])
    assert result["completeness"] == 0.5
    assert result["required_field_accuracy"] == 0.5


def test_deterministic_demo():
    cases_a = generate_cases(10, seed=7)
    cases_b = generate_cases(10, seed=7)
    assert cases_a == cases_b
    assert [offline_predict(c, seed=7) for c in cases_a] == [offline_predict(c, seed=7) for c in cases_b]


def test_aggregate_metrics():
    cases = generate_cases(20, seed=42)
    from app.evaluator import evaluate_case
    results = [evaluate_case(c, offline_predict(c, seed=42)) for c in cases]
    metrics = aggregate_results(results)
    assert metrics["case_count"] == 20
    assert 0 <= metrics["field_accuracy"] <= 1
    assert metrics["defect_count"] > 0
