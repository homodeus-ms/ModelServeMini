import logging
import os
import app.core.logging
import app.db.models

from app.db.session import SessionLocal
from app.kafka.consumer import run_training_consumer
from app.domain.training_batch import service as completion_service

logger = logging.getLogger(__name__)


def process_completed_training_job(training_job_id: int) -> None:

    db = SessionLocal()

    try:
        logger.info(
            "start completion process: training_job_id=%s",
            training_job_id,
        )

        completion_service.process_training_job_completion(
            db,
            training_job_id,
        )

        logger.info(
            "completion process done: training_job_id=%s",
            training_job_id,
        )

    except Exception as exc:
        logger.exception(exc)
        raise

    finally:
        db.close()


def main() -> None:
    run_training_consumer(
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        topic=os.environ["KAFKA_TOPIC"],
        group_id=os.environ["KAFKA_GROUP_ID"],
        process_job=process_completed_training_job,
    )


if __name__ == "__main__":
    main()