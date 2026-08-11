from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, BigInteger, String, DateTime, func, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.time import utc_now
from app.db.base import BaseEntity


class TrainingJob(BaseEntity):
    __tablename__ = "training_jobs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    training_batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_batches.id"),
        nullable=False,
    )

    model_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("models.id"),
        nullable=False,
    )

    dataset_version_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dataset_versions.id"),
        nullable=False,
    )

    requested_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("members.id"),
        nullable=False,
    )

    algorithm: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    target_column: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    completion_counted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    training_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    failure_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now()
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
