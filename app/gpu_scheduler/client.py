import os
import time
import httpx

from app.gpu_scheduler.schema import GpuTaskType


GPU_SCHEDULER_URL = os.getenv(
    "GPU_SCHEDULER_URL",
    "http://localhost:8010",
)

ACQUIRE_RETRY_INTERVAL = 0.2


# gpu-worker, gpu-inference -> GpuScheduler Client -> (http call) -> GpuScheduler Main(Router)

def acquire_gpu(task_id: str, task_type: GpuTaskType, resume: bool = False) -> None:

    while True:
        response = httpx.post(
            f"{GPU_SCHEDULER_URL}/gpu/acquire",
            json={ "task_id": task_id, "task_type": task_type.value, "resume": resume,},
            timeout=5.0,
        )

        response.raise_for_status()

        result = response.json()

        if result["granted"]:
            return

        time.sleep(ACQUIRE_RETRY_INTERVAL)


def release_gpu(task_id: str) -> None:

    response = httpx.post(
        f"{GPU_SCHEDULER_URL}/gpu/release",
        json={ "task_id": task_id },
        timeout=5.0,
    )

    response.raise_for_status()


def should_yield_gpu(task_id: str) -> bool:
    response = httpx.get(
        f"{GPU_SCHEDULER_URL}/gpu/should-yield/{task_id}",
        timeout=5.0,
    )

    response.raise_for_status()

    return response.json()["should_yield"]