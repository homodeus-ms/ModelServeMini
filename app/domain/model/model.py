from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.base import BaseEntity


class Model(BaseEntity):
    __tablename__ = "models"

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

    task_type: Mapped[str]