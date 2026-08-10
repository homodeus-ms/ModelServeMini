from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseEntity


class TrainingBatch(BaseEntity):
    __tablename__ = "training_batches"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    requested_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("members.id"),
        nullable=False,
    )

    dataset_version_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dataset_versions.id"),
        nullable=False,
    )

    target_column: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    total_jobs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    completed_jobs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    recommendation: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )