from uuid import UUID

from fastapi import status

from app.core.exceptions import AppException


class TrainingBatchNotFound(AppException):

    def __init__(self, training_batch_id: UUID):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training batch not found",
            training_batch_id=training_batch_id
        )