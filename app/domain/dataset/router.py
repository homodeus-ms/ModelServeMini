# app/domain/dataset/router.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.dataset import service
from app.domain.dataset.schema import CreateDatasetRequest, DatasetResponse, UpdateDatasetRequest


router = APIRouter(
    prefix="/datasets",
    tags=["datasets"]
)


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> DatasetResponse:
    return service.get_dataset(db, dataset_id)


@router.get("", response_model=list[DatasetResponse])
def get_datasets(created_by: int | None = None, db: Session = Depends(get_db)) -> list[DatasetResponse]:
    return service.get_datasets(db, created_by)


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(request: CreateDatasetRequest, db: Session = Depends(get_db)) -> DatasetResponse:
    return service.create_dataset(db, request)


@router.patch("/{dataset_id}", response_model=DatasetResponse)
def update_dataset(dataset_id: int, request: UpdateDatasetRequest, db: Session = Depends(get_db)) -> DatasetResponse:
    return service.update_dataset(db, dataset_id, request)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)) -> None:
    service.delete_dataset(db, dataset_id)