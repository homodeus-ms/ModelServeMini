from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.model.model import Model


def find_by_id(db: Session, model_id: int) -> Model | None:
    return db.get(Model, model_id)


def find_by_created_by_and_name(db: Session, created_by: int, name: str) -> Model | None:
    stmt = select(Model).where(
        Model.created_by == created_by,
        Model.name == name
    )

    return db.scalar(stmt)


def find_all(db: Session) -> list[Model]:
    stmt = select(Model).order_by(Model.id)
    return list(db.scalars(stmt).all())


def find_all_by_created_by(db: Session, created_by: int) -> list[Model]:
    stmt = (
        select(Model)
        .where(Model.created_by == created_by)
        .order_by(Model.id)
    )

    return list(db.scalars(stmt).all())


def save(db: Session, model: Model) -> Model:
    db.add(model)
    db.flush()
    return model


def delete(db: Session, model: Model) -> None:
    db.delete(model)