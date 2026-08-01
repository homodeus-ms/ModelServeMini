from fastapi import status

from app.core.exceptions import AppException


class ModelNotFound(AppException):

    def __init__(self, model_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
            model_id=model_id
        )


class ModelAlreadyExists(AppException):

    def __init__(self, created_by: int, name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Model already exists",
            created_by=created_by,
            name=name
        )