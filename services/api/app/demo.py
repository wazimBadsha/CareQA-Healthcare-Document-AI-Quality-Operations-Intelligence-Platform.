"""Deterministic synthetic benchmark and offline prediction adapter."""
from __future__ import annotations
import random
from typing import Any

FIELDS = ("claim_reference", "provider", "service_date", "claim_amount", "currency", "claim_type")


def generate_cases(count: int = 24, seed: int = 42) -> list[dict[str, Any]]:
    if count < 1 or count > 10000:
        raise ValueError("count must be between 1 and 10000")
    rng = random.Random(seed)
    providers = ["Al Noor Medical Centre", "Crescent Health Clinic", "Harbour Medical Group", "Oasis Care Centre"]
    types = ["Outpatient", "Inpatient", "Dental", "Pharmacy"]
    cases = []
    for index in range(1, count + 1):
        reference = {
            "claim_reference": f"CLM-{index:05d}",
            "provider": rng.choice(providers),
            "service_date": f"2026-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "claim_amount": f"{rng.randint(100, 9500)}.{rng.randint(0,99):02d}",
            "currency": "AED",
            "claim_type": rng.choice(types),
        }
        # Source text is artificial and contains no real patient information.
        source_text = " | ".join(f"{key}: {value}" for key, value in reference.items())
        cases.append({"case_id": f"case-{index:05d}", "document_type": "synthetic_claim", "source_text": source_text, "reference": reference, "required_fields": list(FIELDS)})
    return cases


def offline_predict(case: dict[str, Any], defect_rate: float = 0.12, seed: int = 42) -> dict[str, Any]:
    """A deterministic mock adapter; controlled defects make metrics demonstrable."""
    rng = random.Random(f"{seed}:{case['case_id']}")
    prediction = dict(case["reference"])
    if rng.random() < defect_rate:
        field = rng.choice(["provider", "service_date", "claim_amount", "claim_type"])
        if field == "claim_amount":
            prediction[field] = f"{float(prediction[field]) + 25.0:.2f}"
        elif field == "provider":
            prediction[field] = "Unknown Provider"
        elif field == "service_date":
            prediction[field] = "2026-01-01"
        else:
            prediction[field] = "Unknown"
    if rng.random() < defect_rate / 2:
        prediction.pop("claim_type", None)
    return prediction


def run_demo(count: int = 24, seed: int = 42) -> dict[str, Any]:
    from .evaluator import evaluate_case, aggregate_results
    cases = generate_cases(count=count, seed=seed)
    results = [evaluate_case(case, offline_predict(case, seed=seed)) for case in cases]
    return {"dataset": {"name": "CareQA Synthetic Claims Benchmark", "version": "1.0.0", "seed": seed, "case_count": count}, "model": {"provider": "offline-mock", "model": "deterministic-baseline", "prompt_version": "offline-v1"}, "metrics": aggregate_results(results), "results": results}
