from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domain.dataset_version.enums import DatasetVersionStatus


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    created_by: int
    version: int

    original_filename: str
    storage_uri: str
    file_size: int
    content_type: str
    checksum: str | None

    status: DatasetVersionStatus

    row_count: int | None
    column_count: int | None
    schema_definition: dict[str, Any] | None
    validation_report: dict[str, Any] | None

    created_at: datetime