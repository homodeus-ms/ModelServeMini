import os
import time
import httpx

from app.core.config import settings
from app.gpu_scheduler.schema import GpuTaskType


GPU_SCHEDULER_URL = settings.gpu_scheduler_url

ACQUIRE_RETRY_INTERVAL = 0.1


def acquire_gpu(task_id: str, task_type: GpuTaskType) -> None:

    while True:
        response = httpx.post(
            f"{GPU_SCHEDULER_URL}/gpu/acquire",
            json={ "task_id": task_id, "task_type": task_type.value},
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