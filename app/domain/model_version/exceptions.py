from fastapi import status

from app.core.exceptions import AppException


class ModelVersionNotFound(AppException):

    def __init__(self, model_version_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model version not found",
            model_version_id=model_version_id
        )


class ModelVersionAlreadyExists(AppException):

    def __init__(self, training_job_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Model version already exists for training job",
            training_job_id=training_job_id
        )


class TrainingJobNotSucceeded(AppException):

    def __init__(self, training_job_id: int, current_status: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Training job has not succeeded",
            training_job_id=training_job_id,
            current_status=current_status
        )


class ArtifactAlreadyExists(AppException):

    def __init__(self, artifact_uri: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Artifact URI already exists",
            artifact_uri=artifact_uri
        )