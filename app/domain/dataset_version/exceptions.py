from fastapi import status

from app.core.exceptions import AppException


class DatasetVersionNotFound(AppException):

    def __init__(self, dataset_version_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset version not found",
            dataset_version_id=dataset_version_id
        )


class DatasetFileRequired(AppException):

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset file is required"
        )


class UnsupportedDatasetFile(AppException):

    def __init__(self, filename: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported",
            filename=filename
        )


class DatasetFileSaveFailed(AppException):

    def __init__(self, filename: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save dataset file",
            filename=filename
        )

class DatasetFileNotFound(AppException):

    def __init__(self, storage_uri: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored dataset file not found",
            storage_uri=storage_uri
        )


class DatasetVersionNotValidatable(AppException):

    def __init__(self, dataset_version_id: int, current_status: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dataset version cannot be validated in its current status",
            dataset_version_id=dataset_version_id,
            current_status=current_status
        )