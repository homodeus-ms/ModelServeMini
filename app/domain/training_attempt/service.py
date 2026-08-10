from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.domain.training_attempt import repository
from app.domain.training_attempt.enums import TrainingAttemptStatus
from app.domain.training_attempt.model import TrainingAttempt


def create_attempt(db: Session, training_job_id: int) -> TrainingAttempt:
    attempt = TrainingAttempt(
        training_job_id=training_job_id,
        attempt_number=repository.find_next_attempt_number(db, training_job_id),
        status=TrainingAttemptStatus.PENDING.value
    )
    return repository.save(db, attempt)


def mark_running(attempt: TrainingAttempt) -> None:
    attempt.status = TrainingAttemptStatus.RUNNING.value
    attempt.started_at = utc_now()


def mark_succeeded(attempt: TrainingAttempt) -> None:
    attempt.status = TrainingAttemptStatus.SUCCEEDED.value
    attempt.finished_at = utc_now()
    attempt.exit_code = 0
    attempt.failure_reason = None


def mark_failed(attempt: TrainingAttempt, failure_reason: str, exit_code: int | None = 1) -> None:
    attempt.status = TrainingAttemptStatus.FAILED.value
    attempt.finished_at = utc_now()
    attempt.exit_code = exit_code
    attempt.failure_reason = failure_reason