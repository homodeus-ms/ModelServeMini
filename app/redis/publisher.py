import json
from typing import Any

from app.redis.client import redis_client
from app.redis.consts import TRAINING_BATCH_EVENTS_CHANNEL


def publish_training_batch_event(
    training_batch_id,
    training_job_id: int,
    completed_jobs: int,
    total_jobs: int,
    status: str,
    recommendation: dict[str, Any] | None = None,
) -> None:

    event = {
        "training_batch_id": str(training_batch_id),
        "training_job_id": training_job_id,
        "completed_jobs": completed_jobs,
        "total_jobs": total_jobs,
        "status": status,
    }

    if recommendation is not None:
        event["recommendation"] = recommendation

    redis_client.publish(
        TRAINING_BATCH_EVENTS_CHANNEL,
        json.dumps(event),
    )