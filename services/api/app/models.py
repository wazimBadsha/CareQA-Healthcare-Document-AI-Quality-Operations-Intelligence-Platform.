import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .database import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


def uuid_str() -> str:
    return str(uuid.uuid4())


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Tenant(Timestamped, Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(24), default="active")


class Dataset(Timestamped, Base):
    __tablename__ = "datasets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(80))
    content_hash: Mapped[str] = mapped_column(String(64))
    schema_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    cases: Mapped[list["DatasetCase"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("tenant_id", "name", "version", name="uq_dataset_version"),)


class DatasetCase(Timestamped, Base):
    __tablename__ = "dataset_cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), index=True)
    case_key: Mapped[str] = mapped_column(String(100))
    document_type: Mapped[str] = mapped_column(String(80))
    reference_json: Mapped[dict] = mapped_column(JSONType)
    source_text: Mapped[str] = mapped_column(Text)
    dataset: Mapped[Dataset] = relationship(back_populates="cases")
    __table_args__ = (UniqueConstraint("dataset_id", "case_key", name="uq_dataset_case_key"),)


class Document(Timestamped, Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    dataset_case_id: Mapped[str | None] = mapped_column(ForeignKey("dataset_cases.id"), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default="ingested")
    extracted_text: Mapped[str] = mapped_column(Text)


class ModelConfig(Timestamped, Base):
    __tablename__ = "model_configs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80), default="offline")
    model_name: Mapped[str] = mapped_column(String(120), default="deterministic-baseline")
    config_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    secret_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)


class EvaluationRun(Timestamped, Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), index=True)
    model_config_id: Mapped[str | None] = mapped_column(ForeignKey("model_configs.id"), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(120))
    prompt_hash: Mapped[str] = mapped_column(String(64))
    evaluator_version: Mapped[str] = mapped_column(String(120))
    code_version: Mapped[str] = mapped_column(String(80), default="local")
    random_seed: Mapped[int] = mapped_column(Integer)
    environment_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Prediction(Timestamped, Base):
    __tablename__ = "predictions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("dataset_cases.id"), index=True)
    output_json: Mapped[dict] = mapped_column(JSONType)
    summary_text: Mapped[str] = mapped_column(Text, default="")
    latency_ms: Mapped[int] = mapped_column(Integer)
    token_usage_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)


class FieldResult(Timestamped, Base):
    __tablename__ = "field_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    prediction_id: Mapped[str] = mapped_column(ForeignKey("predictions.id"), index=True)
    field_path: Mapped[str] = mapped_column(String(160))
    expected_value: Mapped[object] = mapped_column(JSONType)
    actual_value: Mapped[object] = mapped_column(JSONType)
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    metric_json: Mapped[dict] = mapped_column(JSONType, default=dict)


class RunMetric(Timestamped, Base):
    __tablename__ = "run_metrics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    metric_name: Mapped[str] = mapped_column(String(100))
    metric_value: Mapped[float] = mapped_column(Float)
    metric_unit: Mapped[str] = mapped_column(String(32), default="ratio")
    __table_args__ = (UniqueConstraint("run_id", "metric_name", name="uq_run_metric"),)


class AuditEvent(Timestamped, Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(36))
    metadata_json: Mapped[dict] = mapped_column(JSONType, default=dict)


