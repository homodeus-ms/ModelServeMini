import logging
import os
import app.core.logging

from app.db.session import SessionLocal
from app.kafka.consumer import run_training_consumer
from app.training import processor
from app.training import cpu_trainer

logger = logging.getLogger(__name__)

def process_cpu_training_job(training_job_id: int) -> None:
    db = SessionLocal()
    logger.info(f"start job no: {training_job_id}")

    try:
        # 여기에 CPU consumer가 할 일 정의
        processor.process_training_job(db, training_job_id, cpu_trainer.train)
        logger.info(f"{training_job_id} is done by CPUWorker")

    except Exception as e:
        logger.exception(e)
        raise

    finally:
        db.close()

def main() -> None:
    run_training_consumer(
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        topic=os.environ["KAFKA_TOPIC"],
        group_id=os.environ["KAFKA_GROUP_ID"],
        process_job=process_cpu_training_job,
    )


if __name__ == "__main__":
    main()