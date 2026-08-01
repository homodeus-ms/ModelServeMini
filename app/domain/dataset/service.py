from sqlalchemy.orm import Session

from app.domain.dataset import repository
from app.domain.dataset.exceptions import DatasetAlreadyExists, DatasetNotFound
from app.domain.dataset.model import Dataset
from app.domain.dataset.schema import CreateDatasetRequest, UpdateDatasetRequest
from app.domain.member import repository as member_repository
from app.domain.member.exceptions import MemberNotFound


def _get_dataset_or_throw(db: Session, dataset_id: int) -> Dataset:
    dataset = repository.find_by_id(db, dataset_id)

    if dataset is None:
        raise DatasetNotFound(dataset_id)

    return dataset


def _validate_dataset_name(db: Session, created_by: int, name: str, current_dataset_id: int | None = None) -> None:
    existing_dataset = repository.find_by_created_by_and_name(db, created_by, name)

    if existing_dataset is not None and existing_dataset.id != current_dataset_id:
        raise DatasetAlreadyExists(created_by, name)


def get_dataset(db: Session, dataset_id: int) -> Dataset:
    return _get_dataset_or_throw(db, dataset_id)


def get_datasets(db: Session, created_by: int | None = None) -> list[Dataset]:
    if created_by is not None:
        return repository.find_all_by_created_by(db, created_by)

    return repository.find_all(db)


def create_dataset(db: Session, request: CreateDatasetRequest) -> Dataset:
    member = member_repository.find_by_id(db, request.created_by)

    if member is None:
        raise MemberNotFound(request.created_by)

    _validate_dataset_name(db, request.created_by, request.name)

    dataset = Dataset(
        created_by=request.created_by,
        name=request.name,
        description=request.description
    )

    repository.save(db, dataset)

    db.commit()
    db.refresh(dataset)

    return dataset


def update_dataset(db: Session, dataset_id: int, request: UpdateDatasetRequest) -> Dataset:
    dataset = _get_dataset_or_throw(db, dataset_id)
    update_data = request.model_dump(exclude_unset=True)

    if "name" in update_data:
        _validate_dataset_name(db, dataset.created_by, update_data["name"], dataset.id)

    for field, value in update_data.items():
        setattr(dataset, field, value)

    db.commit()
    db.refresh(dataset)

    return dataset


def delete_dataset(db: Session, dataset_id: int) -> None:
    dataset = _get_dataset_or_throw(db, dataset_id)

    repository.delete(db, dataset)
    db.commit()