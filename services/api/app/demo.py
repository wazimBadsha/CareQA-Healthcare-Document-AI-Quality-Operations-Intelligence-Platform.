"""Compatibility helpers for the original offline CareQA demo surface.

The HTTP application now persists datasets and run results. These helpers retain a
small pure-Python generator for notebooks and do not perform database writes.
"""
from .synthetic import generate_cases


def offline_predict(case, seed: int = 42):
    from .evaluator import OfflineAdapter
    return OfflineAdapter().predict(case.reference, seed, case.case_key)[0]
