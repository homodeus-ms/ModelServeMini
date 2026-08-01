
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.dataset.model import Dataset


def find_by_id(db: Session, dataset_id: int) -> Dataset | None:
    return db.get(Dataset, dataset_id)


def find_by_created_by_and_name(db: Session, created_by: int, name: str) -> Dataset | None:
    stmt = select(Dataset).where(
        Dataset.created_by == created_by,
        Dataset.name == name
    )

    return db.scalar(stmt)


def find_all(db: Session) -> list[Dataset]:
    stmt = select(Dataset).order_by(Dataset.id)
    return list(db.scalars(stmt).all())


def find_all_by_created_by(db: Session, created_by: int) -> list[Dataset]:
    stmt = (
        select(Dataset)
        .where(Dataset.created_by == created_by)
        .order_by(Dataset.id)
    )

    return list(db.scalars(stmt).all())


def save(db: Session, dataset: Dataset) -> Dataset:
    db.add(dataset)
    db.flush()
    return dataset


def delete(db: Session, dataset: Dataset) -> None:
    db.delete(dataset)