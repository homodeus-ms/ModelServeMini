from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint(
            "model_id",
            "version",
            name="uq_model_versions_model_id_version"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

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

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    artifact_uri: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True
    )

    artifact_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True
    )

    artifact_checksum: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True
    )

    algorithm: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    training_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False
    )

    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False
    )

    input_schema: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )