import json
import logging
import os

from confluent_kafka import Producer

from app.core.config import settings

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = settings.kafka_bootstrap_servers

_producer = Producer(
    {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    }
)

def _delivery_report(error, message) -> None:
    if error is not None:
        print(f"Kafka message delivery failed: {error}", flush=True)
        return

    print(
        f"Kafka message delivered: "
        f"topic={message.topic()}, "
        f"partition={message.partition()}, "
        f"offset={message.offset()}",
        flush=True,
    )

def publish_training_job(topic: str, training_job_id: int, partition_no: int | None) -> None:
    _publish(
        topic=topic,
        payload={"training_job_id": training_job_id},
        key=str(training_job_id),
        partition_no=partition_no,
    )

def publish_training_job_completed(training_job_id: int) -> None:
    _publish(
        topic="training-job-completed",
        payload={"training_job_id": training_job_id},
        key=str(training_job_id),
    )


# def publish_training_batch_event(training_batch_id,
#                                  training_job_id: int,
#                                  completed_jobs: int,
#                                  total_jobs: int,
#                                  status: str,
#                                  recommendation: dict | None = None) -> None:
#     payload = {
#         "training_batch_id": str(training_batch_id),
#         "training_job_id": training_job_id,
#         "completed_jobs": completed_jobs,
#         "total_jobs": total_jobs,
#         "status": status,
#     }
#
#     if recommendation is not None:
#         payload["recommendation"] = recommendation
#
#     _publish(
#         topic="training-batch-events",
#         payload=payload,
#         key=str(training_batch_id),
#     )

def _publish(topic: str, payload: dict, key: str, partition_no: int | None = None) -> None:

    kw_args = {
        "topic": topic,
        "key": key,
        "value": json.dumps(payload).encode("utf-8"),
        "callback": _delivery_report,
    }

    if partition_no is not None:
        kw_args["partition"] = partition_no

    _producer.produce(**kw_args)

    logger.info(f"published topic: {topic}, key: {key}")

    _producer.poll(0)
    _producer.flush()