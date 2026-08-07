import logging

from dns.dnssecalgs import algorithms
from sqlalchemy.orm import Session

from app.domain.dataset_version import repository as dataset_version_repository
from app.domain.dataset_version.exceptions import DatasetVersionNotFound

from app.domain.training_job import repository as training_job_repository
from app.domain.training_job.exceptions import TrainingJobNotFound

from app.domain.training_job import service as training_job_service

from app.domain.training_attempt import service as attempt_service
from app.domain.training_attempt import repository as attempt_repository
from app.domain.training_job.model import TrainingJob
from app.domain.training_job.schema import CreateTrainingJobRequest
from app.kafka.common import get_training_topic, CPU_TOPIC
from app.kafka.producer import publish_training_job

from app.training.completion_service import (
    complete_training_job,
    fail_training_job
)
from app.training.consts import ALGORITHMS_BY_TASK_TYPE, DEFAULT_CLASSIFICATION_SELECTION_METRIC, \
    DEFAULT_REGRESSION_SELECTION_METRIC, CURRENT_ALGORITHM_COUNT, CPU_ALGORITHM_COUNT
from app.training.exceptions import NotValidTaskType
from app.training.schema import (TrainingRequest, TrainingFailureResult,
                                 TrainingResultResponse, TrainModelsResponse, Recommendation,
                                 TrainingModelAsyncResponse, TrainingModelSummaryInfo)

from app.domain.model.enums import ModelTaskType
from app.domain.training_job.enums import TrainingAlgorithm

logger = logging.getLogger(__name__)

def process_trainings_by_request(db: Session, request: TrainingRequest, member_id: int) -> TrainingModelAsyncResponse:

    algorithm_list = ALGORITHMS_BY_TASK_TYPE.get(request.task_type)
    if (algorithm_list is None) or (len(algorithm_list) == 0):
        raise NotValidTaskType("Task type not supported")

    # 이 함수로 들어오는 요청은 아직 trainig_job 객체 먼저 생성해야함
    training_jobs = list[TrainingJob]()

    for algorithm in algorithm_list:
        try:
            training_jobs.append(training_job_service.create_training_job(db,
                CreateTrainingJobRequest(
                    model_id=request.model_id, dataset_version_id=request.dataset_ver_id,
                    requested_by=member_id, base_model_version_id=request.base_model_version_id,
                    algorithm=algorithm, target_column=request.target_field,
                    training_config=request.training_config,
                )))

        except Exception as exc:
            raise

    assert len(training_jobs) == CURRENT_ALGORITHM_COUNT, f"training_jobs count {len(training_jobs)} != CURRENT_ALGORITHM_COUNT"

    # 카프카 produce
    partition_no = 0

    for training_job in training_jobs:
        topic = get_training_topic(training_job.algorithm)

        logger.info(f"topic: {topic}, training_job_id: {training_job.id}, algorithm: {training_job.algorithm}")

        if topic == CPU_TOPIC:
            partition_no = (partition_no + 1) % CPU_ALGORITHM_COUNT
            publish_training_job(
                topic=topic,
                training_job_id=training_job.id, partition_no=partition_no)
        else:
            publish_training_job(
                topic=topic,
                training_job_id=training_job.id, partition_no=0)


    return TrainingModelAsyncResponse(
        training_jobs=[
            TrainingModelSummaryInfo(
                training_job_id=training_job.id,
                algorithm=training_job.algorithm,
                status=training_job.status,
            )
            for training_job in training_jobs
        ]
    )



    successes = list[TrainingResultResponse]()
    failures = list[TrainingFailureResult]()

    # 일단 단일스레드 순차 진행 -> TODO: 이후 병렬처리로 변경
    for training_job in training_jobs:
        try:
            result = process_training_job(db, training_job.id)
            successes.append(result)

        except Exception as exc:
            failures.append(
                TrainingFailureResult(
                    training_job_id=training_job.id,
                    algorithm=training_job.algorithm,
                    error_message=str(exc)
                )
            )

    recommendation = _get_recommendation(successes, request.task_type)

    return TrainModelsResponse(
        model_id=request.model_id,
        total_train_try_count=len(training_jobs),
        success_count=len(successes),
        successes=successes,
        failure_count=len(failures),
        failures=failures,
        recommendation = recommendation
    )



# ===== 함수 요약 =====
# 1. 트레이닝 재료 준비(trainig_attempt 객체 생성, training_job, dataset_version가져옴) + 상태 변경
# 2. train
# 3. 성공시 model_version, training_job_model_version 객체 생성함, 실패시 롤백
def process_training_job(db: Session, training_job_id: int, train_func) -> TrainingResultResponse:

    attempt = attempt_service.create_attempt(db, training_job_id)
    attempt_service.mark_running(attempt)

    # 함수 내부에서 commit됨 (서비스 함수중 쓰기 함수는 기본적으로 함수 내부에서 커밋함)
    # attemp와 training_job state running 변경은 밑의 작업과는 별도로 저장되는 게 논리적으로 말이됨
    training_job = training_job_service.mark_training_job_running(db, training_job_id)

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
        )

        attempt_service.mark_succeeded(attempt)

        # 여기서 complete_training_job에서 생성된 model_version, 관계객체 등과 함께 커밋
        db.commit()

        # 사용자에게 필요한 정보만 따로 뽑아서 리턴
        return TrainingResultResponse(
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

        # 내부에서 commit함
        fail_training_job(db, training_job_id, str(exc))
        raise

def _get_recommendation(list: list[TrainingResultResponse],
                         task_type: ModelTaskType) -> Recommendation | None:
    if len(list) == 0:
        return None

    best_algorithm = list[0].algorithm
    best_model_ver_id = list[0].model_version_id
    criterion_metric = DEFAULT_CLASSIFICATION_SELECTION_METRIC \
        if task_type == ModelTaskType.CLASSIFICATION \
        else DEFAULT_REGRESSION_SELECTION_METRIC

    max_value = list[0].metrics.get(criterion_metric, float("-inf"))

    for train_result in list:
        value = train_result.metrics.get(criterion_metric, float("-inf"))
        if value > max_value:
            max_value = value
            best_algorithm = train_result.algorithm
            best_model_ver_id = train_result.model_version_id

    return Recommendation(
        model_version_id=best_model_ver_id,
        algorithm=best_algorithm,
        criterion_metric=criterion_metric,
        metric_score=max_value,
    )

