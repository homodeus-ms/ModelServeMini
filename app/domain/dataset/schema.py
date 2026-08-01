from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateDatasetRequest(BaseModel):
    created_by: int
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class UpdateDatasetRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime