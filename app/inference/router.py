from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.inference import service
from app.inference.schema import (
    InferenceRequest,
    InferenceResponse
)


router = APIRouter(
    prefix="/inference",
    tags=["Inference"]
)


@router.post("/predict", response_model=InferenceResponse)
def predict(request: InferenceRequest, db: Session = Depends(get_db)) -> InferenceResponse:
    return service.predict(db, request)