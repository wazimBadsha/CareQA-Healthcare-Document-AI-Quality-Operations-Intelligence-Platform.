from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Dataset, DatasetCase, ModelConfig, Tenant
from .synthetic import dataset_hash, generate_cases


def get_or_create_tenant(db: Session, slug: str = "demo") -> Tenant:
    tenant = db.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant:
        return tenant
    tenant = Tenant(slug=slug, name="CareQA Demo Workspace")
    db.add(tenant)
    db.flush()
    db.add(ModelConfig(tenant_id=tenant.id, provider="offline", model_name="deterministic-baseline", config_json={"mode": "offline"}))
    db.commit()
    db.refresh(tenant)
    return tenant


def create_synthetic_dataset(db: Session, tenant: Tenant, name: str, version: str, count: int, seed: int) -> Dataset:
    cases = generate_cases(count, seed)
    dataset = Dataset(
        tenant_id=tenant.id,
        name=name,
        version=version,
        content_hash=dataset_hash(cases),
        schema_json={"required_fields": list(cases[0].reference), "generator": "careqa.synthetic.v1", "seed": seed},
    )
    db.add(dataset)
    db.flush()
    for case in cases:
        db.add(DatasetCase(dataset_id=dataset.id, case_key=case.case_key, document_type=case.document_type,
                           reference_json=case.reference, source_text=case.source_text))
    db.commit()
    db.refresh(dataset)
    return dataset


def seed_demo(db: Session) -> None:
    tenant = get_or_create_tenant(db)
    exists = db.scalar(select(Dataset).where(Dataset.tenant_id == tenant.id).limit(1))
    if not exists:
        create_synthetic_dataset(db, tenant, "Synthetic CareQA benchmark", "v1", 24, 2026)


