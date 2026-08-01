from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TrainingJobModelVersion(Base):
    __tablename__ = "training_job_model_versions"
    __table_args__ = (
        CheckConstraint(
            "relation_type IN ('BASE', 'RESULT')",
            name="ck_training_job_model_versions_relation_type"
        ),
    )

    training_job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("training_jobs.id"),
        primary_key=True
    )

    relation_type: Mapped[str] = mapped_column(
        String(20),
        primary_key=True
    )

    model_version_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("model_versions.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )