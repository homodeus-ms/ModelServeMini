from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.training_batch.model import TrainingBatch


def find_by_id(db: Session, training_batch_id: UUID) -> TrainingBatch | None:
    stmt = (select(TrainingBatch).where(TrainingBatch.id == training_batch_id))

    return db.scalar(stmt)

def find_all_by_requested_by(db: Session, requested_by: int) -> list[TrainingBatch]:

    stmt = (
        select(TrainingBatch)
        .where(
            TrainingBatch.requested_by == requested_by
        )
        .order_by(
            TrainingBatch.created_at.desc()
        )
    )

    return list(db.scalars(stmt).all())


def save(db: Session, training_batch: TrainingBatch) -> TrainingBatch:

    db.add(training_batch)
    db.flush()

    return training_batch