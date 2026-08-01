from fastapi import status

from app.core.exceptions import AppException


class TrainingJobNotFound(AppException):

    def __init__(self, training_job_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training job not found",
            training_job_id=training_job_id
        )


class DatasetVersionNotReady(AppException):

    def __init__(self, dataset_version_id: int, current_status: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dataset version is not ready",
            dataset_version_id=dataset_version_id,
            current_status=current_status
        )


class AlgorithmNotCompatible(AppException):

    def __init__(self, task_type: str, algorithm: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Algorithm is not compatible with model task type",
            task_type=task_type,
            algorithm=algorithm
        )


class TrainingJobCannotBeCancelled(AppException):

    def __init__(self, training_job_id: int, current_status: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Training job cannot be cancelled",
            training_job_id=training_job_id,
            current_status=current_status
        )


class InvalidTrainingJobState(AppException):

    def __init__(self, training_job_id: int, current_status: str, target_status: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid training job state transition",
            training_job_id=training_job_id,
            current_status=current_status,
            target_status=target_status
        )