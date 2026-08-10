
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.model.enums import ModelTaskType
from app.domain.training_batch.enums import TrainingBatchStatus
from app.domain.training_batch.model import TrainingBatch
from app.domain.training_batch import repository
from app.domain.training_batch.exceptions import TrainingBatchNotFound
from app.domain.training_batch.schema import TrainingBatchResultResponse, TrainingBatchResultItem
from app.domain.training_job import repository as training_job_repository
from app.domain.training_job.enums import TrainingJobStatus
from app.domain.training_job.exceptions import TrainingJobNotFound
from app.domain.model_version import repository as model_version_repository
from app.redis.publisher import publish_training_batch_event

from app.training.consts import DEFAULT_CLASSIFICATION_SELECTION_METRIC, DEFAULT_REGRESSION_SELECTION_METRIC
from app.training.recommendation import RecommendationCandidate, get_recommendation
from app.training.schema import Recommendation


def create_training_batch(
    db: Session,
    requested_by: int,
    dataset_version_id: int,
    target_column: str,
    task_type: str,
    total_jobs: int,
) -> TrainingBatch:

    training_batch = TrainingBatch(
        requested_by=requested_by,
        dataset_version_id=dataset_version_id,
        target_column=target_column,
        task_type=task_type,
        status="PENDING",
        total_jobs=total_jobs,
        completed_jobs=0,
    )

    return repository.save(
        db,
        training_batch,
    )


def increment_completed_jobs(training_batch: TrainingBatch) -> None:

    if training_batch.completed_jobs >= training_batch.total_jobs:
        return

    training_batch.completed_jobs += 1

    if training_batch.completed_jobs == training_batch.total_jobs:
        training_batch.status = "SUCCEEDED"
        training_batch.completed_at = datetime.now(timezone.utc)


def mark_running(training_batch: TrainingBatch) -> None:

    if training_batch.status == "PENDING":
        training_batch.status = "RUNNING"


def get_training_batch(db: Session, training_batch_id: UUID) -> TrainingBatch:
    training_batch = repository.find_by_id(db, training_batch_id)

    if training_batch is None:
        raise TrainingBatchNotFound(training_batch_id=training_batch_id)

    return training_batch



# 각 학습 worker들의 일 종료 -> completion_consumer가 이 함수를 호출함
# 한 training_batch에 속한 각각의 학습을 관리함
# 완료된 갯수를 1 증가 SSE publish
def process_training_job_completion(db: Session, training_job_id: int) -> None:

    training_job = training_job_repository.find_by_id(db, training_job_id)
    if training_job is None:
        raise TrainingJobNotFound(training_job_id=training_job_id)

    # 카프카 중복 메시지 방지
    if training_job.completion_counted:
        return

    training_batch = repository.find_by_id(db, training_job.training_batch_id)
    if training_batch is None:
        raise TrainingBatchNotFound(training_batch_id=training_job.training_batch_id)

    # 해당 Job 완료 처리
    # TODO: 이후에 completion-worker를 여러개 쓰게 되면 여기 동시성 처리 필요
    training_job.completion_counted = True
    training_batch.completed_jobs += 1

    recommendation: Recommendation | None = None

    # 모든 학습이 끝난 경우에만 최종 상태 결정 + Recommendation
    if training_batch.completed_jobs == training_batch.total_jobs:

        training_jobs = training_job_repository.find_all_by_batch_id(
            db,
            training_batch.id,
        )

        has_failed_job = any(
            job.status == TrainingJobStatus.FAILED.value
            for job in training_jobs
        )

        if has_failed_job:
            training_batch.status = TrainingBatchStatus.FAILED.value
        else:
            training_batch.status = TrainingBatchStatus.SUCCEEDED.value

            # 이번 Batch에서 생성된 ModelVersion들 조회
            model_versions = (model_version_repository
                              .find_result_versions_by_training_batch_id(db, training_batch.id))

            candidates = [RecommendationCandidate(algorithm=model_version.algorithm,
                                                  model_version_id=model_version.id,
                                                  metrics=model_version.metrics)
                          for model_version in model_versions]

            recommendation = get_recommendation(candidates=candidates,
                                                task_type=ModelTaskType(training_batch.task_type))

            if recommendation is not None:
                training_batch.recommendation = recommendation.model_dump()


        training_batch.completed_at = datetime.now(timezone.utc)


    db.commit()

    # SSE 이벤트 발행 -> Redis로
    publish_training_batch_event(training_batch_id=training_batch.id,
                                 training_job_id=training_job.id,
                                 completed_jobs=training_batch.completed_jobs,
                                 total_jobs=training_batch.total_jobs,
                                 status=training_batch.status,
                                 recommendation=(recommendation.model_dump() if recommendation is not None else None),
    )


def get_training_batch_result(db: Session, training_batch_id: UUID) -> TrainingBatchResultResponse:

    training_batch = repository.find_by_id(db, training_batch_id)

    if training_batch is None:
        raise TrainingBatchNotFound(training_batch_id)

    training_jobs = training_job_repository.find_all_by_batch_id(db, training_batch_id)

    results: list[TrainingBatchResultItem] = []

    for training_job in training_jobs:
        model_version = model_version_repository.find_result_by_training_job_id(
                db,
                training_job.id)

        if model_version is None:
            continue

        results.append(
            TrainingBatchResultItem(
                training_job_id=training_job.id,
                model_version_id=model_version.id,
                algorithm=model_version.algorithm,
                metrics=model_version.metrics,
                feature_columns=model_version.feature_columns,
                feature_importances=model_version.feature_importances,
                artifact_uri=model_version.artifact_uri,
            )
        )

        metric_name = DEFAULT_CLASSIFICATION_SELECTION_METRIC \
            if training_batch.task_type == "CLASSIFICATION" \
            else DEFAULT_REGRESSION_SELECTION_METRIC

        results.sort(key=lambda result: result.metrics.get(metric_name, float("-inf")), reverse=True)

    return TrainingBatchResultResponse(
        training_batch_id=training_batch.id,
        status=training_batch.status,
        recommendation=training_batch.recommendation,
        results=results,
    )

def get_training_batches_by_member(db: Session, member_id: int) -> list[TrainingBatch]:

    return repository.find_all_by_requested_by(db, member_id)