"""Deterministic, fictional benchmark fixture generator. No patient data."""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class SyntheticCase:
    case_key: str
    document_type: str
    source_text: str
    reference: dict


FACILITIES = ("Northstar Clinic", "Harborview Centre", "Cedar Health Lab")
DIAGNOSES = ("hypertension", "type 2 diabetes", "asthma", "hyperlipidemia")
MEDICATIONS = ("metformin", "lisinopril", "atorvastatin", "albuterol")
CONDITIONS = ("blood pressure monitoring", "medication reconciliation", "follow-up scheduling", "lifestyle counselling")


def generate_cases(count: int, seed: int) -> list[SyntheticCase]:
    if not 1 <= count <= 1_000:
        raise ValueError("count must be between 1 and 1000")
    rng = random.Random(seed)
    cases: list[SyntheticCase] = []
    for index in range(1, count + 1):
        encounter = date(2026, 1, 1) + timedelta(days=index % 120)
        diagnosis = rng.choice(DIAGNOSES)
        medication = rng.choice(MEDICATIONS)
        conditions = rng.sample(CONDITIONS, k=2)
        reference = {
            "document_id": f"SYN-{seed}-{index:04d}",
            "encounter_date": encounter.isoformat(),
            "facility": rng.choice(FACILITIES),
            "diagnosis": diagnosis,
            "medication": medication,
            "dosage_mg": rng.choice((5, 10, 20, 40, 500)),
            "follow_up_days": rng.choice((7, 14, 30, 90)),
            "conditions": conditions,
        }
        source = (
            f"SYNTHETIC TRAINING DOCUMENT — Case {reference['document_id']}. "
            f"Encounter date: {reference['encounter_date']}. Facility: {reference['facility']}. "
            f"Assessment: {diagnosis}. Medication: {medication} {reference['dosage_mg']} mg. "
            f"Follow-up in {reference['follow_up_days']} days. Care actions: {', '.join(conditions)}."
        )
        cases.append(SyntheticCase(f"case-{index:04d}", "synthetic_follow_up_note", source, reference))
    return cases


def dataset_hash(cases: list[SyntheticCase]) -> str:
    stable = [{"key": c.case_key, "reference": c.reference, "source": c.source_text} for c in cases]
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()
