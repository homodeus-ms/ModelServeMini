from typing import Any

from app.core.time import utc_now
from app.domain.training_job.enums import TrainingJobStatus
from app.domain.training_job.exceptions import InvalidTrainingJobState
from app.domain.training_job.model import TrainingJob


def mark_running(training_job: TrainingJob) -> None:
    _ensure_status(training_job, {TrainingJobStatus.PENDING, TrainingJobStatus.FAILED}, TrainingJobStatus.RUNNING)

    now = utc_now()
    if training_job.queued_at is not None and now < training_job.queued_at:
        now = training_job.queued_at
    training_job.status = TrainingJobStatus.RUNNING.value
    training_job.started_at = now


def mark_succeeded(training_job: TrainingJob, metrics: dict[str, Any]) -> None:
    _ensure_status(training_job, TrainingJobStatus.RUNNING, TrainingJobStatus.SUCCEEDED)

    training_job.status = TrainingJobStatus.SUCCEEDED.value
    training_job.metrics = metrics
    training_job.failure_message = None

    now = utc_now()
    if training_job.started_at is not None and now < training_job.started_at:
        now = training_job.started_at
    training_job.finished_at = now


def mark_failed(training_job: TrainingJob, failure_message: str) -> None:
    _ensure_status(training_job, TrainingJobStatus.RUNNING, TrainingJobStatus.FAILED)

    training_job.status = TrainingJobStatus.FAILED.value
    training_job.failure_message = failure_message
    training_job.finished_at = utc_now()


def cancel(training_job: TrainingJob) -> None:
    _ensure_status(training_job, TrainingJobStatus.PENDING, TrainingJobStatus.CANCELLED)

    training_job.status = TrainingJobStatus.CANCELLED.value
    training_job.finished_at = utc_now()


def _ensure_status(training_job: TrainingJob, required: TrainingJobStatus | set[TrainingJobStatus],
                   target: TrainingJobStatus) -> None:

    if isinstance(required, TrainingJobStatus):
        allowed = {required.value}
    else:
        allowed = {status.value for status in required}

    if training_job.status not in allowed:
        raise InvalidTrainingJobState(
            training_job.id,
            training_job.status,
            target.value
        )