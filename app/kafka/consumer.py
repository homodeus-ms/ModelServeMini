import json
import logging
from typing import Callable

from confluent_kafka import Consumer, KafkaException, KafkaError

logger = logging.getLogger(__name__)

def run_training_consumer(
        *,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        process_job: Callable[[int], None]
) -> None:

    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        # 학습 성공 후에 수동 커밋
        "enable.auto.commit": False,
    })

    consumer.subscribe([topic])

    logger.info(f"Consumer started: topic={topic}, group_id={group_id}")

    try:
        while True:
            message = consumer.poll(timeout=1.0)
            if message is None:
                continue

            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise RuntimeError(message.error())

            payload = json.loads(message.value().decode('utf-8'))
            training_job_id = int(payload['training_job_id'])

            try:
                process_job(training_job_id)

                # 학습과 DB상태 변경이 성공한 경우에만 offset 커밋
                consumer.commit(message=message, asynchronous=False)

            except Exception as exc:
                logger.exception(exc)
                consumer.commit(message=message, asynchronous=False)

    except Exception as exc:
        logger.exception(exc)

    finally:
        consumer.close()


