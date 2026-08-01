from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.training_attempt.model import TrainingAttempt


def find_by_id(db: Session, attempt_id: int) -> TrainingAttempt | None:
    return db.get(TrainingAttempt, attempt_id)


def find_all_by_training_job_id(db: Session, training_job_id: int) -> list[TrainingAttempt]:
    stmt = (
        select(TrainingAttempt)
        .where(TrainingAttempt.training_job_id == training_job_id)
        .order_by(TrainingAttempt.attempt_number)
    )
    return list(db.scalars(stmt).all())


def find_next_attempt_number(db: Session, training_job_id: int) -> int:
    stmt = select(
        func.coalesce(func.max(TrainingAttempt.attempt_number), 0) + 1
    ).where(
        TrainingAttempt.training_job_id == training_job_id
    )

    result = db.scalar(stmt)
    return int(result or 1)


def save(db: Session, attempt: TrainingAttempt) -> TrainingAttempt:
    db.add(attempt)
    db.flush()
    return attempt