from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.model_version import service
from app.domain.model_version.schema import ModelVersionResponse

router = APIRouter(
    prefix="/model-versions",
    tags=["Model Versions"]
)


@router.get("/{model_version_id}", response_model=ModelVersionResponse)
def get_model_version(
    model_version_id: int,
    db: Session = Depends(get_db)
) -> ModelVersionResponse:
    return service.get_model_version(
        db,
        model_version_id
    )


@router.get("", response_model=list[ModelVersionResponse])
def get_model_versions(
    model_id: int = Query(gt=0),
    db: Session = Depends(get_db)
) -> list[ModelVersionResponse]:
    return service.get_model_versions(
        db,
        model_id
    )

@router.get("{model_version_id}/deploy", response_model=ModelVersionResponse)
def deploy_model_version(model_version_id: int, db: Session = Depends(get_db)):
    return service.deploy_model_version(db, model_version_id)