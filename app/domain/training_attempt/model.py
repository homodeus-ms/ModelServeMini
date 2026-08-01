from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TrainingAttempt(Base):
    __tablename__ = "training_attempts"
    __table_args__ = (
        UniqueConstraint(
            "training_job_id",
            "attempt_number",
            name="uq_training_attempts_job_attempt_number"
        ),
        CheckConstraint(
            "attempt_number > 0",
            name="ck_training_attempts_attempt_number"
        ),
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED')",
            name="ck_training_attempts_status"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    training_job_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("training_jobs.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)

    kubernetes_job_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pod_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gpu_node_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gpu_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    checkpoint_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    log_uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )