from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.model import service
from app.domain.model.schema import CreateModelRequest, ModelResponse, UpdateModelRequest


router = APIRouter(
    prefix="/models",
    tags=["Models"]
)


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(model_id: int, db: Session = Depends(get_db)) -> ModelResponse:
    return service.get_model(db, model_id)


@router.get("", response_model=list[ModelResponse])
def get_models(created_by: int | None = Query(default=None, gt=0), db: Session = Depends(get_db)) -> list[ModelResponse]:
    return service.get_models(db, created_by)


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def create_model(request: CreateModelRequest, db: Session = Depends(get_db)) -> ModelResponse:
    return service.create_model(db, request)


@router.patch("/{model_id}", response_model=ModelResponse)
def update_model(model_id: int, request: UpdateModelRequest, db: Session = Depends(get_db)) -> ModelResponse:
    return service.update_model(db, model_id, request)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_model(db, model_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)