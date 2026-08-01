from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.dataset_version import service
from app.domain.dataset_version.schema import DatasetVersionResponse


router = APIRouter(
    prefix="/dataset-versions",
    tags=["dataset-versions"]
)


@router.get("/{dataset_version_id}", response_model=DatasetVersionResponse)
def get_dataset_version(dataset_version_id: int, db: Session = Depends(get_db)) -> DatasetVersionResponse:
    return service.get_dataset_version(db, dataset_version_id)


@router.get("", response_model=list[DatasetVersionResponse])
def get_dataset_versions(dataset_id: int, db: Session = Depends(get_db)) -> list[DatasetVersionResponse]:
    return service.get_dataset_versions(db, dataset_id)


@router.post("", response_model=DatasetVersionResponse, status_code=status.HTTP_201_CREATED)
def create_dataset_version(
    dataset_id: int = Form(...),
    created_by: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> DatasetVersionResponse:
    return service.create_dataset_version(db, dataset_id, created_by, file)

@router.post("/{dataset_version_id}/validate", response_model=DatasetVersionResponse)
def validate_dataset_version(dataset_version_id: int, db: Session = Depends(get_db)) -> DatasetVersionResponse:
    return service.validate_dataset_version(db, dataset_version_id)

@router.delete("/{dataset_version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset_version(dataset_version_id: int, db: Session = Depends(get_db)) -> None:
    service.delete_dataset_version(db, dataset_version_id)