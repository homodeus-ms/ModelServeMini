import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.dataset_version import repository as dataset_version_repository
from app.domain.dataset_version.exceptions import DatasetVersionNotFound

from app.domain.training_job import service as training_job_service

from app.domain.training_attempt import service as attempt_service
from app.domain.training_attempt import repository as attempt_repository
from app.domain.training_job.enums import TrainingAlgorithm
from app.domain.training_job.model import TrainingJob
from app.domain.training_job.schema import CreateTrainingJobRequest
from app.kafka.common import get_training_topic, CPU_TOPIC, GPU_TOPIC, CPU_TOPIC_PARTITION_COUNT
from app.kafka.producer import publish_training_job, publish_training_job_completed

from app.training.completion_service import (
    complete_training_job,
    fail_training_job
)
from app.training.algorithm_registry import ALGORITHMS_BY_TASK_TYPE, get_algorithms_by_task_type
from app.training.exceptions import NotValidTaskType
from app.training.schema import (TrainingRequest,
                                 TrainingResultResponse,
                                 TrainingModelAsyncResponse, TrainingModelSummaryInfo)

from app.domain.training_batch import service as training_batch_service

logger = logging.getLogger(__name__)



def process_trainings_by_request(db: Session, request: TrainingRequest, member_id: int) -> TrainingModelAsyncResponse:

    logger.info("== process_trainings_by_request start ==")

    algorithm_list = get_algorithms_by_task_type(task_type=request.task_type,
                                                 enable_gpu=settings.enable_gpu_training)

    if (algorithm_list is None) or (len(algorithm_list) == 0):
        raise NotValidTaskType("Task type not supported")

    # 1. 사용자 요청 단위 Batch 생성
    training_batch = training_batch_service.create_training_batch(
        db=db,
        requested_by=member_id,
        dataset_version_id=request.dataset_ver_id,
        target_column=request.target_field,
        task_type=request.task_type.value,
        total_jobs=len(algorithm_list),
    )

    # 2. 알고리듬별 trainig_job 생성
    training_jobs = list[TrainingJob]()

    for algorithm in algorithm_list:
        try:
            training_jobs.append(
                training_job_service.create_training_job(
                    db,
                    CreateTrainingJobRequest(
                        model_id=request.model_id, dataset_version_id=request.dataset_ver_id,
                        requested_by=member_id, base_model_version_id=request.base_model_version_id,
                        algorithm=algorithm, target_column=request.target_field,
                        training_config=request.training_config,
                    ),
                    training_batch.id))

        except Exception as exc:
            raise

    # 3. Batch RUNNING
    training_batch_service.mark_running(training_batch)

    db.commit()

    # 4. commit 성공 후 카프카 produce
    partition_no = 0

    for training_job in training_jobs:
        topic = get_training_topic(training_job.algorithm)

        logger.info(f"topic: {topic}, training_job_id: {training_job.id}, algorithm: {training_job.algorithm}")

        if topic == CPU_TOPIC:
            partition_no = (partition_no + 1) % CPU_TOPIC_PARTITION_COUNT
            publish_training_job(
                topic=topic,
                training_job_id=training_job.id, partition_no=partition_no)
        else:
            publish_training_job(
                topic=topic,
                training_job_id=training_job.id, partition_no=0)


    return TrainingModelAsyncResponse(
        training_batch_id=training_batch.id,
        training_jobs=[
            TrainingModelSummaryInfo(
                training_job_id=training_job.id,
                algorithm=training_job.algorithm,
                status=training_job.status,
            )
            for training_job in training_jobs
        ]
    )



# ===== 함수 요약 =====
# 1. 트레이닝 재료 준비(trainig_attempt 객체 생성, training_job, dataset_version가져옴) + 상태 변경
# 2. train
# 3. 성공시 model_version, training_job_model_version 객체 생성함, 실패시 롤백
def process_training_job(db: Session, training_job_id: int, train_func) -> TrainingResultResponse:

    attempt = attempt_service.create_attempt(db, training_job_id)
    attempt_service.mark_running(attempt)

    # attemp와 training_job state running 변경은 밑의 작업과는 별도로 여기서 커밋
    training_job = training_job_service.mark_training_job_running(db, training_job_id)
    db.commit()

    attempt_id = attempt.id

    try:
        dataset_version = dataset_version_repository.find_by_id(
            db,
            training_job.dataset_version_id
        )

        if dataset_version is None:
            raise DatasetVersionNotFound(
                training_job.dataset_version_id
            )

        training_result = train_func(training_job, dataset_version)


        # model_verison, training_job_model_version 객체 생성, metrics는 model_version안으로 들어감
        model_version = complete_training_job(
            db=db,
            training_job_id=training_job.id,
            artifact_uri=training_result.artifact_uri,
            artifact_size=training_result.artifact_size,
            artifact_checksum=training_result.artifact_checksum,
            metrics=training_result.metrics,
            input_schema=training_result.input_schema,
            feature_columns=training_result.feature_columns,
            feature_importances=training_result.feature_importances,
        )

        attempt_service.mark_succeeded(attempt)

        # 여기서 complete_training_job에서 생성된 model_version, 관계객체 등과 함께 커밋
        db.commit()

        # 여러개의 trainging_job을 총괄하는 일감 publish
        publish_training_job_completed(training_job_id=training_job.id)

        # 사용자에게 필요한 정보만 따로 뽑아서 리턴
        return TrainingResultResponse(
            training_batch_id=training_job.training_batch_id,
            training_job_id=training_job.id,
            algorithm=training_job.algorithm,
            model_version_id=model_version.id,
            artifact_uri=model_version.artifact_uri,
            metrics=model_version.metrics,
            feature_columns=model_version.feature_columns,
            feature_importances=training_result.feature_importances,
        )

    except Exception as exc:

        db.rollback()

        attempt = attempt_repository.find_by_id(db, attempt_id)
        if attempt is not None:
            attempt_service.mark_failed(attempt, str(exc))

        fail_training_job(db, training_job_id, str(exc))
        db.commit()

        publish_training_job_completed(training_job_id=training_job.id)

        raise


def execute_training_job_by_id(db: Session, training_job_id: int) -> TrainingModelSummaryInfo:

    training_job = training_job_service.get_training_job(db, training_job_id)
    algorithm = TrainingAlgorithm(training_job.algorithm)
    topic = get_training_topic(algorithm)

    if topic == CPU_TOPIC:
        publish_training_job(
            topic=CPU_TOPIC,
            training_job_id=training_job.id,
            partition_no=0,
        )

    elif topic == GPU_TOPIC:
        publish_training_job(
            topic=GPU_TOPIC,
            training_job_id=training_job.id,
            partition_no=0,
        )

    else:
        raise ValueError(f"Unsupported training topic for algorithm: {algorithm}")

    return TrainingModelSummaryInfo(
        training_job_id=training_job.id,
        algorithm=training_job.algorithm,
        status=training_job.status)

