import json
import logging
import os

from confluent_kafka import Producer

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

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
    payload = {"training_job_id": training_job_id}

    if partition_no is None:
        _producer.produce(
            topic=topic,
            key=str(training_job_id),
            value=json.dumps(payload).encode("utf-8"),
            callback=_delivery_report,
        )
    else:
        _producer.produce(
            topic=topic,
            partition=partition_no,
            key=str(training_job_id),
            value=json.dumps(payload).encode("utf-8"),
            callback=_delivery_report,
        )

    logger.info(f"published training job {training_job_id} to topic {topic} and partition {partition_no}")

    _producer.poll(0)

    # 현재 API 요청에서는 Kafka 전송 성공 여부를 확인하기 위해 flush
    _producer.flush()