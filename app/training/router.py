from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.training import processor

router = APIRouter(
    prefix="/training-jobs",
    tags=["Training Jobs"]
)

@router.post("/training-jobs/{training_job_id}/execute")
def execute_training_job(training_job_id: int, db: Session = Depends(get_db)):

    processor.process_training_job(
        db,
        training_job_id
    )

    return {
        "message": "training completed"
    }