from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseEntity


class Dataset(BaseEntity):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)

    created_by: Mapped[int] = mapped_column(
        ForeignKey("members.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str | None]

    creator = relationship("Member")
