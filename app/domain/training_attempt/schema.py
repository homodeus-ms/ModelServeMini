from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.training_attempt.enums import TrainingAttemptStatus


class TrainingAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    training_job_id: int
    attempt_number: int
    status: TrainingAttemptStatus

    kubernetes_job_name: str | None
    pod_name: str | None
    gpu_node_name: str | None
    gpu_type: str | None

    checkpoint_uri: str | None
    log_uri: str | None

    started_at: datetime | None
    finished_at: datetime | None
    exit_code: int | None
    failure_reason: str | None
    created_at: datetime