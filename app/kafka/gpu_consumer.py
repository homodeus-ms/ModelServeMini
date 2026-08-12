import logging
import os
from typing import Callable

import app.core.logging
import app.db.models

from app.db.session import SessionLocal
from app.domain.training_job.enums import TrainingAlgorithm
from app.gpu_scheduler.client import acquire_gpu, release_gpu
from app.gpu_scheduler.schema import GpuTaskType
from app.kafka.consumer import run_training_consumer
from app.training import processor, gpu_trainer
from app.training.pytorch import trainer as pytorch_trainer
from app.domain.training_job import service as training_job_service

logger = logging.getLogger(__name__)

def process_gpu_training_job(training_job_id: int) -> None:

    db = SessionLocal()
    task_id = f"training-{training_job_id}"
    gpu_acquired = False

    try:
        logger.info("requested GPU: task_id=%s", task_id)
        acquire_gpu(task_id=task_id, task_type=GpuTaskType.TRAINING)
        gpu_acquired = True
        logger.info("GPU acquired: task_id=%s", task_id)

        training_job = training_job_service.get_training_job(db, training_job_id)
        algorithm = TrainingAlgorithm(training_job.algorithm)
        train_function = _get_gpu_train_function(algorithm)

        processor.process_training_job(db, training_job_id, train_function)
        logger.info("%s is done by GPU Worker", training_job_id)

    except Exception as e:
        logger.exception(e)
        raise

    finally:
        if gpu_acquired:
            try:
                release_gpu(task_id)
                logger.info("GPU released: task_id=%s", task_id)
            except Exception:
                logger.exception("failed to release GPU: task_id=%s", task_id)

        db.close()

def _get_gpu_train_function(algorithm: TrainingAlgorithm) -> Callable:
    if algorithm in {
        TrainingAlgorithm.PYTORCH_MLP_CLASSIFIER,
        TrainingAlgorithm.PYTORCH_MLP_REGRESSOR,
    }:
        return pytorch_trainer.train

    return gpu_trainer.train


def main() -> None:
    run_training_consumer(
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        topic=os.environ["KAFKA_TOPIC"],
        group_id=os.environ["KAFKA_GROUP_ID"],
        process_job=process_gpu_training_job,
    )

if __name__ == "__main__":
    main()