from fastapi import FastAPI, HTTPException

from app.gpu_scheduler import service
from app.gpu_scheduler.schema import (
    AcquireGpuRequest,
    AcquireGpuResponse,
    GpuSchedulerStatusResponse,
    ReleaseGpuRequest, ShouldYieldResponse,
)


app = FastAPI(
    title="ModelServeMini GPU Scheduler",
)


@app.post("/gpu/acquire", response_model=AcquireGpuResponse)
def acquire_gpu(request: AcquireGpuRequest) -> AcquireGpuResponse:
    return service.acquire(request)


@app.post("/gpu/release")
def release_gpu(request: ReleaseGpuRequest) -> dict:

    released = service.release(request.task_id)

    if not released:
        raise HTTPException(status_code=409, detail="Task does not own GPU")

    return {"released": True, "task_id": request.task_id}


@app.get("/gpu/status", response_model=GpuSchedulerStatusResponse)
def get_gpu_status() -> GpuSchedulerStatusResponse:
    return service.get_status()

@app.get("/gpu/should-yield/{task_id}", response_model=ShouldYieldResponse)
def should_yield(task_id: str) -> ShouldYieldResponse:
    return service.should_yield(task_id)