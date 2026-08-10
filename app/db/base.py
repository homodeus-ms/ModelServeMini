from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.time import utc_now


class Base(DeclarativeBase):
    pass

class BaseEntity(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )