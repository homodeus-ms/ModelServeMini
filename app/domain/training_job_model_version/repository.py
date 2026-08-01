from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.training_job_model_version.model import TrainingJobModelVersion


def find_by_job_and_type(db: Session, training_job_id: int, relation_type: str) -> TrainingJobModelVersion | None:
    stmt = select(TrainingJobModelVersion).where(
        TrainingJobModelVersion.training_job_id == training_job_id,
        TrainingJobModelVersion.relation_type == relation_type
    )
    return db.scalar(stmt)


def find_all_by_training_job_id(db: Session, training_job_id: int) -> list[TrainingJobModelVersion]:
    stmt = select(TrainingJobModelVersion).where(
        TrainingJobModelVersion.training_job_id == training_job_id
    )
    return list(db.scalars(stmt).all())


def find_all_by_model_version_id(db: Session, model_version_id: int) -> list[TrainingJobModelVersion]:
    stmt = select(TrainingJobModelVersion).where(
        TrainingJobModelVersion.model_version_id == model_version_id
    )
    return list(db.scalars(stmt).all())


def save(db: Session, relation: TrainingJobModelVersion) -> TrainingJobModelVersion:
    db.add(relation)
    db.flush()
    return relation