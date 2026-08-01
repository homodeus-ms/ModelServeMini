from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.member.model import Member


def find_by_id(db: Session, member_id: int) -> Member | None:
    return db.get(Member, member_id)


def find_by_email(db: Session, email: str) -> Member | None:
    stmt = select(Member).where(Member.email == email)
    return db.scalar(stmt)


def find_all(db: Session) -> list[Member]:
    stmt = select(Member)
    return list(db.scalars(stmt).all())


def save(db: Session, member: Member) -> Member:
    db.add(member)
    db.flush()

    return member


def delete(db: Session, member: Member) -> None:
    db.delete(member)