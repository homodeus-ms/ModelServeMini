import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.model import repository as model_repository
from app.domain.model.exceptions import ModelNotFound
from app.domain.model_version import repository
from app.domain.model_version.enums import DeploymentStatus
from app.domain.model_version.exceptions import (
    ArtifactAlreadyExists,
    ModelVersionAlreadyExists,
    ModelVersionNotFound
)
from app.domain.model_version.mapper import model_version_to_cache_dto
from app.domain.model_version.model import ModelVersion
from app.domain.model_version.schema import CreateModelVersionData, ModelVersionCache
from app.domain.training_job import repository as training_job_repository
from app.domain.training_job.enums import TrainingJobStatus
from app.domain.training_job.exceptions import (
    InvalidTrainingJobState,
    TrainingJobNotFound
)
from app.redis.cache import set_deployed_model_version_redis

logger = logging.getLogger(__name__)


def get_model_version(db: Session, model_version_id: int) -> ModelVersion:
    return _get_model_version_or_throw(db, model_version_id)


def get_model_versions(db: Session, model_id: int) -> list[ModelVersion]:
    model = model_repository.find_by_id(db, model_id)

    if model is None:
        raise ModelNotFound(model_id)

    return repository.find_all_by_model_id(db, model_id)



def deploy_model_version(db: Session, model_version_id: int) -> ModelVersion:

    try:
        model_version = repository.find_by_id(db, model_version_id)

        if model_version is None:
            raise ModelVersionNotFound(model_version_id)

        prev_deployed_version = repository.find_deploy_version_by_id(db, model_version.model_id)
        
        if prev_deployed_version is not None:
            prev_deployed_version.deployment_status = DeploymentStatus.ARCHIVED.value
            db.flush()

        model_version.deployment_status = DeploymentStatus.PRODUCTION.value

        db.commit()

    except:
        db.rollback()
        raise

    _cache_deployed_version_to_redis(model_version)

    return model_version


def create_model_version(db: Session, data: CreateModelVersionData) -> ModelVersion:
    training_job = training_job_repository.find_by_id(db, data.training_job_id)

    if training_job is None:
        raise TrainingJobNotFound(data.training_job_id)

    if training_job.status != TrainingJobStatus.RUNNING.value:
        raise InvalidTrainingJobState(
            training_job.id,
            training_job.status,
            TrainingJobStatus.SUCCEEDED.value
        )

    existing_model_version = repository.find_result_by_training_job_id(
        db,
        training_job.id
    )

    if existing_model_version is not None:
        raise ModelVersionAlreadyExists(training_job.id)

    existing_artifact = repository.find_by_artifact_uri(
        db,
        data.artifact_uri
    )

    if existing_artifact is not None:
        raise ArtifactAlreadyExists(data.artifact_uri)

    # DB 락 획득
    repository.acquire_version_lock(db, training_job.model_id)

    next_version = repository.find_next_version(
        db,
        training_job.model_id
    )

    model_version = ModelVersion(
        model_id=training_job.model_id,
        dataset_version_id=training_job.dataset_version_id,
        version=next_version,
        artifact_uri=data.artifact_uri,
        artifact_size=data.artifact_size,
        artifact_checksum=data.artifact_checksum,
        algorithm=training_job.algorithm,
        training_config=training_job.training_config,
        metrics=data.metrics,
        input_schema=data.input_schema,
        feature_columns=data.feature_columns,
        feature_importances=data.feature_importances,
        deployment_status=DeploymentStatus.NONE.value,
    )

    try:
        repository.save(db, model_version)

        return model_version

    except IntegrityError as exc:
        db.rollback()
        print(exc.orig)
        raise


    
def _get_model_version_or_throw(db: Session, model_version_id: int) -> ModelVersion:
    model_version = repository.find_by_id(db, model_version_id)

    if model_version is None:
        raise ModelVersionNotFound(model_version_id)

    return model_version

def _cache_deployed_version_to_redis(model_version: ModelVersion):
    try:
        cached = model_version_to_cache_dto(model_version)
        set_deployed_model_version_redis(model_version.model_id,cached)

    except Exception:
        logger.exception("Failed to update deployed model cache: " "model_id=%s, model_version_id=%s",
            model_version.model_id, model_version.id)