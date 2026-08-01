from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.training_job.enums import TrainingAlgorithm, TrainingJobStatus


class CreateTrainingJobRequest(BaseModel):
    model_id: int = Field(gt=0)
    dataset_version_id: int = Field(gt=0)
    requested_by: int = Field(gt=0)

    base_model_version_id: int | None = Field(default=None, gt=0)

    algorithm: TrainingAlgorithm

    target_column: str = Field(
        min_length=1,
        max_length=200
    )

    training_config: dict[str, Any] = Field(default_factory=dict)


class TrainingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    model_id: int
    dataset_version_id: int
    requested_by: int

    algorithm: TrainingAlgorithm
    target_column: str
    status: TrainingJobStatus

    training_config: dict[str, Any]
    metrics: dict[str, Any] | None
    failure_message: str | None

    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime