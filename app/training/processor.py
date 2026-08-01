from sqlalchemy.orm import Session

from app.domain.dataset_version import repository as dataset_version_repository
from app.domain.dataset_version.exceptions import DatasetVersionNotFound

from app.domain.training_job import repository as training_job_repository
from app.domain.training_job.exceptions import TrainingJobNotFound

from app.domain.training_job import service as training_job_service

from app.domain.training_attempt import service as attempt_service
from app.domain.training_attempt import repository as attempt_repository
from app.domain.training_job.model import TrainingJob

from app.training.completion_service import (
    complete_training_job,
    fail_training_job
)

from app.training.trainer import train


def process_training_job(db: Session, training_job_id: int) -> None:

    attempt = attempt_service.create_attempt(db, training_job_id)
    attempt_service.mark_running(attempt)

    # 함수 내부에서 commit (서비스 함수중 쓰기 함수는 기본적으로 함수 내부에서 커밋함)
    training_job = training_job_service.mark_training_job_running(db, training_job_id)

    attempt_id = attempt.id

    try:
        dataset_version = dataset_version_repository.find_by_id(
            db,
            training_job.dataset_version_id
        )

        if dataset_version is None:
            raise DatasetVersionNotFound(
                training_job.dataset_version_id
            )

        training_result = train(training_job, dataset_version)

        complete_training_job(
            db=db,
            training_job_id=training_job.id,
            artifact_uri=training_result.artifact_uri,
            artifact_size=training_result.artifact_size,
            artifact_checksum=training_result.artifact_checksum,
            metrics=training_result.metrics,
            input_schema=training_result.input_schema
        )

        attempt_service.mark_succeeded(attempt)
        db.commit()

    except Exception as exc:

        db.rollback()

        attempt = attempt_repository.find_by_id(db, attempt_id)
        if attempt is not None:
            attempt_service.mark_failed(attempt, str(exc))

        # commit함
        fail_training_job(db, training_job_id, str(exc))
        raise