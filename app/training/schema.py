from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.model.enums import ModelTaskType


class TrainingRequest(BaseModel):
    model_id: int
    base_model_version_id: int | None = Field(default=None, gt=0)
    dataset_ver_id: int
    training_config: dict[str, Any] = Field(default_factory=dict)
    target_field: str
    task_type: ModelTaskType

class TrainingResultResponse(BaseModel):
    training_batch_id: UUID

    training_job_id: int
    algorithm: str

    model_version_id: int
    artifact_uri: str

    metrics: dict[str, float]
    feature_columns: list[str]
    feature_importances: list[dict[str, float | int | str]] | None = None

class TrainingFailureResult(BaseModel):
    training_job_id: int
    algorithm: str
    error_message: str | None

class Recommendation(BaseModel):
    model_version_id: int | None = None
    algorithm: str
    criterion_metric: str
    metric_score: float

class TrainModelsResponse(BaseModel):
    training_batch_id: UUID

    model_id: int
    total_train_try_count: int
    success_count: int
    successes: list[TrainingResultResponse]
    failure_count: int
    failures: list[TrainingFailureResult]
    recommendation: Recommendation | None = Field(default=None)

class TrainingModelSummaryInfo(BaseModel):
    training_job_id: int
    algorithm: str
    status: str

class TrainingModelAsyncResponse(BaseModel):
    training_batch_id: UUID
    training_jobs: list[TrainingModelSummaryInfo]