# app/domain/training_job/router.py

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.training_job import service
from app.domain.training_job.enums import TrainingJobStatus
from app.domain.training_job.schema import (
    CreateTrainingJobRequest,
    TrainingJobResponse
)

router = APIRouter(
    prefix="/training-jobs",
    tags=["Training Jobs"]
)


@router.get("/{training_job_id}", response_model=TrainingJobResponse)
def get_training_job(training_job_id: int, db: Session = Depends(get_db)) -> TrainingJobResponse:
    return service.get_training_job(db, training_job_id)


@router.get("", response_model=list[TrainingJobResponse])
def get_training_jobs(
    model_id: int | None = Query(default=None, gt=0),
    dataset_version_id: int | None = Query(default=None, gt=0),
    requested_by: int | None = Query(default=None, gt=0),
    job_status: TrainingJobStatus | None = Query(
        default=None,
        alias="status"
    ),
    db: Session = Depends(get_db)
) -> list[TrainingJobResponse]:

    return service.get_training_jobs(
        db=db,
        model_id=model_id,
        dataset_version_id=dataset_version_id,
        requested_by=requested_by,
        status=job_status
    )


@router.post("", response_model=TrainingJobResponse, status_code=status.HTTP_201_CREATED)
def create_training_job(request: CreateTrainingJobRequest, db: Session = Depends(get_db)) -> TrainingJobResponse:
    return service.create_training_job(db, request)


@router.post("/{training_job_id}/cancel", response_model=TrainingJobResponse)
def cancel_training_job(
    training_job_id: int,
    db: Session = Depends(get_db)
) -> TrainingJobResponse:

    return service.cancel_training_job(
        db,
        training_job_id
    )
