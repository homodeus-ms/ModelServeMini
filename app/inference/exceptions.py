from fastapi import status

from app.core.exceptions import AppException

class ModelArtifactNotFound(AppException):
    def __init__(self, artifact_uri: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model artifact not found",
            artifact_uri=artifact_uri
        )


class InvalidInferenceInput(AppException):
    def __init__(
        self,
        missing_columns: list[str] | None = None,
        extra_columns: list[str] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inference input does not match model input schema",
            missing_columns=missing_columns or [],
            extra_columns=extra_columns or []
        )


class NonNumericInferenceInput(AppException):
    def __init__(self, column: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only numeric inference inputs are currently supported",
            column=column
        )


class ModelArtifactLoadFailed(AppException):
    def __init__(self, artifact_uri: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load model artifact",
            artifact_uri=artifact_uri
        )


class InferenceFailed(AppException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inference failed",
            message=message
        )

class InvalidInferenceInputValue(AppException):
    def __init__(self, column: str, value_type: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported inference input value",
            column=column,
            value_type=value_type
        )

class DeployVersionNotFound(AppException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Should Deploy One First",
            message=message
        )