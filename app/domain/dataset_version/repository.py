from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.dataset_version.model import DatasetVersion


def find_by_id(db: Session, dataset_version_id: int) -> DatasetVersion | None:
    return db.get(DatasetVersion, dataset_version_id)


def find_all_by_dataset_id(db: Session, dataset_id: int) -> list[DatasetVersion]:
    stmt = (
        select(DatasetVersion)
        .where(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version.desc())
    )

    return list(db.scalars(stmt).all())


def find_next_version(db: Session, dataset_id: int) -> int:
    stmt = select(func.coalesce(func.max(DatasetVersion.version), 0) + 1).where(
        DatasetVersion.dataset_id == dataset_id
    )

    return db.scalar(stmt) or 1


def save(db: Session, dataset_version: DatasetVersion) -> DatasetVersion:
    db.add(dataset_version)
    db.flush()
    return dataset_version


def delete(db: Session, dataset_version: DatasetVersion) -> None:
    db.delete(dataset_version)