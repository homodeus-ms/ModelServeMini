# app/domain/dataset/exceptions.py

from fastapi import status

from app.core.exceptions import AppException


class DatasetNotFound(AppException):

    def __init__(self, dataset_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
            dataset_id=dataset_id
        )


class DatasetAlreadyExists(AppException):

    def __init__(self, created_by: int, name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dataset already exists",
            created_by=created_by,
            name=name
        )