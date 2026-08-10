import heapq
from itertools import count
from threading import Lock

from app.gpu_scheduler import repository
from app.gpu_scheduler.schema import (
    AcquireGpuRequest,
    AcquireGpuResponse,
    GpuSchedulerStatusResponse,
    GpuTaskType,
    WaitingTask,
)

# 숫자가 작을수록 높은 우선순위
PRIORITY_BY_TASK_TYPE = {
    GpuTaskType.INFERENCE: 0,
    GpuTaskType.TRAINING: 10,
}

def acquire(request: AcquireGpuRequest) -> AcquireGpuResponse:

    priority = PRIORITY_BY_TASK_TYPE[request.task_type]

    granted = repository.acquire_or_enqueue(
        task_id=request.task_id,
        task_type=request.task_type,
        priority=priority,
    )

    owner = repository.get_owner()

    return AcquireGpuResponse(
        granted=granted,
        task_id=request.task_id,
        current_owner=(
            owner["task_id"]
            if owner
            else None
        ),
    )


def release(task_id: str) -> bool:
    released, _next_task = repository.release_and_assign_next(task_id)
    return released



def get_status() -> GpuSchedulerStatusResponse:

    owner = repository.get_owner()
    waiting = repository.get_waiting_tasks()

    return GpuSchedulerStatusResponse(
        current_owner=owner["task_id"] if owner else None,
        current_task_type=(
            GpuTaskType(owner["task_type"])
            if owner
            else None
        ),
        current_priority=(
            int(owner["priority"])
            if owner
            else None
        ),
        waiting_tasks=[
            WaitingTask(
                task_id=task["task_id"],
                task_type=GpuTaskType(task["task_type"]),
                priority=int(task["priority"]),
            ) for task in waiting])


