from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.training_job.model import TrainingJob


def find_by_id(db: Session, training_job_id: int) -> TrainingJob | None:
    return db.get(TrainingJob, training_job_id)


def find_all(
    db: Session,
    model_id: int | None = None,
    dataset_version_id: int | None = None,
    requested_by: int | None = None,
    status: str | None = None
) -> list[TrainingJob]:
    stmt = select(TrainingJob)

    if model_id is not None:
        stmt = stmt.where(TrainingJob.model_id == model_id)

    if dataset_version_id is not None:
        stmt = stmt.where(
            TrainingJob.dataset_version_id == dataset_version_id
        )

    if requested_by is not None:
        stmt = stmt.where(
            TrainingJob.requested_by == requested_by
        )

    if status is not None:
        stmt = stmt.where(TrainingJob.status == status)

    stmt = stmt.order_by(TrainingJob.id.desc())

    return list(db.scalars(stmt).all())


def save(db: Session, training_job: TrainingJob) -> TrainingJob:
    db.add(training_job)
    db.flush()
    return training_job