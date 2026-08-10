from enum import Enum

from pydantic import BaseModel, Field


class GpuTaskType(str, Enum):
    INFERENCE = "INFERENCE"
    TRAINING = "TRAINING"


class AcquireGpuRequest(BaseModel):
    task_id: str = Field(min_length=1)
    task_type: GpuTaskType


class AcquireGpuResponse(BaseModel):
    granted: bool
    task_id: str
    current_owner: str | None = None


class ReleaseGpuRequest(BaseModel):
    task_id: str = Field(min_length=1)


class WaitingTask(BaseModel):
    task_id: str
    task_type: GpuTaskType
    priority: int

class GpuSchedulerStatusResponse(BaseModel):
    current_owner: str | None
    current_task_type: GpuTaskType | None
    current_priority: int | None

    waiting_tasks: list[WaitingTask]



