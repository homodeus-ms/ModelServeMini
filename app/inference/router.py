from fastapi import APIRouter, Depends, Path
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

@router.post("/models/{model_id}/predict", response_model=InferenceResponse)
def predict_by_model(request: InferenceRequest,
            model_id: int = Path(gt=0),
            db: Session = Depends(get_db)) -> InferenceResponse:

    return service.predict_by_model(db, model_id, request)


@router.post("/model_versions/{model_version_id}/predict", response_model=InferenceResponse)
def predict_by_model_version(request: InferenceRequest,
            model_version_id: int = Path(gt=0),
            db: Session = Depends(get_db)) -> InferenceResponse:

    return service.predict_by_model_version(db, model_version_id, request)