import argparse

from .database import Base, SessionLocal, engine
from .evaluator import execute_run, run_metadata
from .models import EvaluationRun
from .seed import create_synthetic_dataset, get_or_create_tenant


def demo(cases: int, seed: int) -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        tenant = get_or_create_tenant(db)
        dataset = create_synthetic_dataset(db, tenant, "CLI synthetic benchmark", f"seed-{seed}", cases, seed)
        run = EvaluationRun(tenant_id=tenant.id, dataset_id=dataset.id, prompt_version="offline-baseline-v1", prompt_hash="cli",
                            evaluator_version="deterministic-fields-v1", random_seed=seed, environment_json=run_metadata(seed))
        db.add(run); db.commit(); db.refresh(run)
        execute_run(db, run)
        print(f"Completed run {run.id} on dataset {dataset.id} ({cases} synthetic cases).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create and evaluate a synthetic CareQA demo benchmark")
    parser.add_argument("demo", nargs="?")
    parser.add_argument("--cases", type=int, default=40)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    demo(args.cases, args.seed)
