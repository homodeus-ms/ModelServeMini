from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.model_version.model import ModelVersion
from app.domain.training_job_model_version.enums import ModelVersionRelationType
from app.domain.training_job_model_version.model import TrainingJobModelVersion


def find_by_id(db: Session, model_version_id: int) -> ModelVersion | None:
    return db.get(ModelVersion, model_version_id)


def find_result_by_training_job_id(db: Session, training_job_id: int) -> ModelVersion | None:
    stmt = (
        select(ModelVersion)
        .join(
            TrainingJobModelVersion,
            TrainingJobModelVersion.model_version_id == ModelVersion.id
        )
        .where(
            TrainingJobModelVersion.training_job_id == training_job_id,
            TrainingJobModelVersion.relation_type == ModelVersionRelationType.RESULT.value
        )
    )

    return db.scalar(stmt)


def find_by_artifact_uri(db: Session, artifact_uri: str) -> ModelVersion | None:
    stmt = select(ModelVersion).where(
        ModelVersion.artifact_uri == artifact_uri
    )

    return db.scalar(stmt)


def find_all_by_model_id(db: Session, model_id: int) -> list[ModelVersion]:
    stmt = (
        select(ModelVersion)
        .where(ModelVersion.model_id == model_id)
        .order_by(ModelVersion.version.desc())
    )

    return list(db.scalars(stmt).all())


def find_next_version(db: Session, model_id: int) -> int:
    stmt = select(
        func.coalesce(func.max(ModelVersion.version), 0) + 1
    ).where(
        ModelVersion.model_id == model_id
    )

    next_version = db.scalar(stmt)

    if next_version is None:
        return 1

    return int(next_version)


def save(db: Session, model_version: ModelVersion) -> ModelVersion:
    db.add(model_version)
    db.flush()

    return model_version