from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.model.enums import ModelTaskType


class CreateModelRequest(BaseModel):
    created_by: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    task_type: ModelTaskType


class UpdateModelRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    task_type: ModelTaskType | None = None


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int
    name: str
    description: str | None
    task_type: ModelTaskType
    created_at: datetime
    updated_at: datetime