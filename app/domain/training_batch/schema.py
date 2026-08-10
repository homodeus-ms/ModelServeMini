from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class TrainingBatchResponse(BaseModel):
    id: UUID

    requested_by: int
    dataset_version_id: int

    target_column: str
    task_type: str

    status: str

    total_jobs: int
    completed_jobs: int

    recommendation: dict[str, Any] | None

    completed_at: datetime | None

    model_config = {
        "from_attributes": True
    }

class TrainingBatchSummaryResponse(BaseModel):
    id: UUID
    target_column: str
    task_type: str
    status: str
    total_jobs: int
    completed_jobs: int
    completed_at: datetime | None


class TrainingBatchResultItem(BaseModel):
    training_job_id: int
    model_version_id: int

    algorithm: str

    metrics: dict[str, Any]

    feature_columns: list[str] | None
    feature_importances: list[dict[str, Any]] | None

    artifact_uri: str



class TrainingBatchResultResponse(BaseModel):
    training_batch_id: UUID

    status: str

    recommendation: dict[str, Any] | None

    results: list[TrainingBatchResultItem]