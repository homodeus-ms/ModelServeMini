from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, BigInteger, String, DateTime, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.base import BaseEntity


class TrainingJob(BaseEntity):
    __tablename__ = "training_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    model_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("models.id"),
        nullable=False
    )

    dataset_version_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dataset_versions.id"),
        nullable=False
    )

    requested_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("members.id"),
        nullable=False
    )

    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    target_column: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)

    training_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False
    )

    metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True
    )

    failure_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
