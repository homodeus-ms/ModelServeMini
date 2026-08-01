from datetime import datetime, timezone
from typing import Any

import transitions
from sqlalchemy.orm import Session

from app.domain.dataset_version import repository as dataset_version_repository
from app.domain.dataset_version.exceptions import DatasetVersionNotFound
from app.domain.member import repository as member_repository
from app.domain.member.exceptions import MemberNotFound
from app.domain.model import repository as model_repository
from app.domain.model.enums import ModelTaskType
from app.domain.model.exceptions import ModelNotFound
from app.domain.model_version.exceptions import ModelVersionNotFound
from app.domain.model_version.model import ModelVersion
from app.domain.model_version import repository as model_version_repository
from app.domain.training_job import repository
from app.domain.training_job.enums import TrainingAlgorithm, TrainingJobStatus
from app.domain.training_job.exceptions import (
    AlgorithmNotCompatible,
    DatasetVersionNotReady,
    InvalidTrainingJobState,
    TrainingJobCannotBeCancelled,
    TrainingJobNotFound
)
from app.domain.training_job.model import TrainingJob
from app.domain.training_job.schema import CreateTrainingJobRequest
from app.domain.training_job import transitions
from app.domain.training_job_model_version import service as relation_service


CLASSIFICATION_ALGORITHMS = {
    TrainingAlgorithm.LOGISTIC_REGRESSION,
    TrainingAlgorithm.RANDOM_FOREST_CLASSIFIER
}

REGRESSION_ALGORITHMS = {
    TrainingAlgorithm.LINEAR_REGRESSION,
    TrainingAlgorithm.RANDOM_FOREST_REGRESSOR
}


def get_training_job(db: Session, training_job_id: int) -> TrainingJob:
    return _get_training_job_or_throw(db, training_job_id)


def get_training_jobs(
    db: Session,
    model_id: int | None = None,
    dataset_version_id: int | None = None,
    requested_by: int | None = None,
    status: TrainingJobStatus | None = None
) -> list[TrainingJob]:
    status_value = status.value if status is not None else None

    return repository.find_all(
        db=db,
        model_id=model_id,
        dataset_version_id=dataset_version_id,
        requested_by=requested_by,
        status=status_value
    )


def create_training_job(db: Session, request: CreateTrainingJobRequest) -> TrainingJob:
    model = _get_model_or_throw(db, request.model_id)

    dataset_version = _get_dataset_version_or_throw(
        db,
        request.dataset_version_id
    )

    _validate_member(db, request.requested_by)
    _validate_dataset_version_ready(dataset_version)
    _validate_algorithm(model.task_type, request.algorithm)

    training_job = TrainingJob(
        model_id=request.model_id,
        dataset_version_id=request.dataset_version_id,
        requested_by=request.requested_by,
        algorithm=request.algorithm.value,
        target_column=request.target_column,
        status=TrainingJobStatus.PENDING.value,
        training_config=request.training_config,
        metrics=None,
        failure_message=None,
        queued_at=transitions._now(),
        started_at=None,
        finished_at=None
    )

    try:
        # training_job과 관계 객체 저장 트랜잭션
        repository.save(db, training_job)

        if request.base_model_version_id is not None:

            _validate_base_model_version(db, request.base_model_version_id, request.model_id)

            relation_service.create_base_relation(
                db,
                training_job.id,
                request.base_model_version_id
            )

        db.commit()
        db.refresh(training_job)

        return training_job

    except Exception:
        db.rollback()
        raise


def cancel_training_job(db: Session, training_job_id: int) -> TrainingJob:
    training_job = _get_training_job_or_throw(
        db,
        training_job_id
    )

    if training_job.status != TrainingJobStatus.PENDING.value:
        raise TrainingJobCannotBeCancelled(
            training_job.id,
            training_job.status
        )

    training_job.status = TrainingJobStatus.CANCELLED.value
    training_job.finished_at = transitions._now()

    db.commit()
    db.refresh(training_job)

    return training_job


def mark_training_job_running(db: Session, training_job_id: int) -> TrainingJob:
    training_job = _get_training_job_or_throw(db, training_job_id)

    transitions.mark_running(training_job)

    db.commit()
    db.refresh(training_job)

    return training_job


def mark_training_job_succeeded(db: Session, training_job_id: int, metrics: dict[str, Any]) -> TrainingJob:
    training_job = _get_training_job_or_throw(db, training_job_id)

    transitions.mark_succeeded(training_job, metrics)

    db.commit()
    db.refresh(training_job)

    return training_job


def mark_training_job_failed(db: Session, training_job_id: int, failure_message: str) -> TrainingJob:
    training_job = _get_training_job_or_throw(db, training_job_id)

    transitions.mark_failed(training_job, f"training job Id: {training_job_id} failed!")

    db.commit()
    db.refresh(training_job)

    return training_job


def _get_training_job_or_throw(db: Session, training_job_id: int) -> TrainingJob:
    training_job = repository.find_by_id(db, training_job_id)

    if training_job is None:
        raise TrainingJobNotFound(training_job_id)

    return training_job


def _get_model_or_throw(db: Session, model_id: int):
    model = model_repository.find_by_id(db, model_id)

    if model is None:
        raise ModelNotFound(model_id)

    return model


def _get_dataset_version_or_throw(db: Session, dataset_version_id: int):
    dataset_version = dataset_version_repository.find_by_id(
        db,
        dataset_version_id
    )

    if dataset_version is None:
        raise DatasetVersionNotFound(dataset_version_id)

    return dataset_version

def _validate_base_model_version(db: Session, model_version_id: int, request_model_id:int):
    base_model_version = model_version_repository.find_by_id(db, model_version_id)

    if base_model_version is None:
        raise ModelVersionNotFound(model_version_id)

    if base_model_version.model_id != request_model_id:
        raise ValueError("Base model version does not belong to the requested model")


def _validate_member(db: Session, member_id: int) -> None:
    member = member_repository.find_by_id(db, member_id)

    if member is None:
        raise MemberNotFound(member_id)


def _validate_dataset_version_ready(dataset_version) -> None:
    if dataset_version.status != "READY":
        raise DatasetVersionNotReady(
            dataset_version.id,
            dataset_version.status
        )


def _validate_algorithm(task_type: str, algorithm: TrainingAlgorithm) -> None:
    if task_type == ModelTaskType.CLASSIFICATION.value:
        if algorithm not in CLASSIFICATION_ALGORITHMS:
            raise AlgorithmNotCompatible(
                task_type,
                algorithm.value
            )

        return

    if task_type == ModelTaskType.REGRESSION.value:
        if algorithm not in REGRESSION_ALGORITHMS:
            raise AlgorithmNotCompatible(
                task_type,
                algorithm.value
            )

        return

    raise AlgorithmNotCompatible(
        task_type,
        algorithm.value
    )

