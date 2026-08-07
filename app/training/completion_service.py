from sqlalchemy.orm import Session

from app.domain.model_version import service as model_version_service
from app.domain.model_version.model import ModelVersion
from app.domain.model_version.schema import CreateModelVersionData
from app.domain.training_job import repository as training_job_repository, transitions
from app.domain.training_job_model_version import service as relation_service
from app.domain.training_job.exceptions import TrainingJobNotFound


def complete_training_job(
    db: Session,
    training_job_id: int,
    artifact_uri: str,
    artifact_size: int | None,
    artifact_checksum: str | None,
    metrics: dict,
    input_schema: dict | None,
    feature_columns: list[str],
) -> ModelVersion:

    # model_version 객체와 training_job_model_version 관계 객체 생성함

    training_job = training_job_repository.find_by_id(
        db,
        training_job_id
    )

    if training_job is None:
        raise TrainingJobNotFound(training_job_id)

    data = CreateModelVersionData(
        training_job_id=training_job_id,
        artifact_uri=artifact_uri,
        artifact_size=artifact_size,
        artifact_checksum=artifact_checksum,
        metrics=metrics,
        input_schema=input_schema,
        feature_columns=feature_columns,
    )

    model_version = model_version_service.create_model_version(db, data)

    relation_service.create_result_relation(
        db,
        training_job_id,
        model_version.id
    )

    transitions.mark_succeeded(training_job, metrics)

    return model_version


def fail_training_job(db: Session, training_job_id: int, failure_message: str) -> None:

    training_job = training_job_repository.find_by_id(
        db,
        training_job_id
    )

    if training_job is None:
        raise TrainingJobNotFound(training_job_id)

    try:
        transitions.mark_failed(
            training_job,
            failure_message
        )

        db.commit()

    except Exception:
        db.rollback()
        raise