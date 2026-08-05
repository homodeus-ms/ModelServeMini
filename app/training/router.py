from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.training import processor
from app.training.schema import TrainingRequest, TrainingResultResponse, TrainModelsResponse

router = APIRouter(
    prefix="/training-jobs",
    tags=["Training Jobs"]
)

@router.post("/{training_job_id}/execute", response_model=TrainingResultResponse)
def execute_training_job(training_job_id: int, db: Session = Depends(get_db)):

    return processor.process_training_job(db, training_job_id)


@router.post("/execute", response_model=TrainModelsResponse)
def execute_trainig_jobs(request: TrainingRequest, member_id:int, db: Session = Depends(get_db)):

    return processor.process_trainings_by_request(db, request, member_id)
