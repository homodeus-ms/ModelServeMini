from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.training_batch import service
from app.domain.training_batch.schema import TrainingBatchResponse, TrainingBatchResultResponse, \
    TrainingBatchSummaryResponse

router = APIRouter(
    prefix="/training-batches",
    tags=["Training Batch"],
)

@router.get("", response_model=list[TrainingBatchSummaryResponse])
def get_training_batches(member_id: int, db: Session = Depends(get_db)):
    return service.get_training_batches_by_member(db, member_id)

@router.get("/{training_batch_id}", response_model=TrainingBatchResponse)
def get_training_batch(training_batch_id: UUID, db: Session = Depends(get_db)) -> TrainingBatchResponse:
    training_batch = service.get_training_batch(db, training_batch_id)
    return TrainingBatchResponse.model_validate(training_batch)

@router.get("/{training_batch_id}/result", response_model=TrainingBatchResultResponse)
def get_training_batch_result(training_batch_id: UUID,
                              db: Session = Depends(get_db)) -> TrainingBatchResultResponse:
    return service.get_training_batch_result(db, training_batch_id)