from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=2, max_length=160)
    version: str = Field(min_length=1, max_length=80)
    schema_definition: dict[str, Any] = Field(
        default_factory=dict, alias="schema_json", serialization_alias="schema_json"
    )


class CaseCreate(BaseModel):
    case_key: str = Field(min_length=1, max_length=100)
    document_type: str = Field(min_length=1, max_length=80)
    reference_json: dict[str, Any]
    source_text: str = Field(min_length=1, max_length=100_000)


class DemoDatasetCreate(BaseModel):
    name: str = "Synthetic CareQA benchmark"
    version: str = "v1"
    cases: int = Field(default=24, ge=1, le=1000)
    seed: int = Field(default=2026, ge=0, le=2_147_483_647)


class RunCreate(BaseModel):
    dataset_id: str
    prompt_version: str = Field(default="offline-baseline-v1", max_length=120)
    evaluator_version: str = Field(default="deterministic-fields-v1", max_length=120)
    seed: int = Field(default=2026, ge=0, le=2_147_483_647)


class DocumentCreate(BaseModel):
    """Text-only synthetic-document ingestion for the offline benchmark."""

    storage_key: str = Field(min_length=1, max_length=255)
    extracted_text: str = Field(min_length=1, max_length=100_000)
    dataset_case_id: str | None = None


class DatasetOut(BaseModel):
    id: str
    name: str
    version: str
    content_hash: str
    case_count: int
    created_at: datetime


class RunOut(BaseModel):
    id: str
    dataset_id: str
    status: str
    prompt_version: str
    evaluator_version: str
    random_seed: int
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None


class MetricOut(BaseModel):
    metric_name: str
    metric_value: float
    metric_unit: str
