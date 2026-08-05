from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreateModelVersionData(BaseModel):
    training_job_id: int = Field(gt=0)

    artifact_uri: str = Field(min_length=1)
    artifact_size: int | None = Field(default=None, ge=0)
    artifact_checksum: str | None = Field(default=None, max_length=128)

    metrics: dict[str, Any]
    input_schema: dict[str, Any] | None = None
    feature_columns: list[str]


class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: int
    dataset_version_id: int

    version: int

    artifact_uri: str
    artifact_size: int | None
    artifact_checksum: str | None

    algorithm: str
    training_config: dict[str, Any]
    metrics: dict[str, Any]
    input_schema: dict[str, Any] | None
    feature_columns: list[str]
    deployment_status: str

    created_at: datetime

