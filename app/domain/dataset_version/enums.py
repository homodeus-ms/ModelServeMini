from enum import Enum


class DatasetVersionStatus(str, Enum):
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    READY = "READY"
    INVALID = "INVALID"
    FAILED = "FAILED"