from sqlalchemy.orm import Session

from app.core.security import password_hasher
from app.domain.member import repository
from app.domain.member.exceptions import MemberAlreadyExists, MemberNotFound
from app.domain.member.model import Member
from app.domain.member.schema import CreateMemberRequest, UpdateMemberRequest


def get_member(db: Session, member_id: int) -> Member:
    member = _get_member_or_throw(db, member_id)
    return member


def get_members(db: Session) -> list[Member]:
    return repository.find_all(db)


def create_member(db: Session, request: CreateMemberRequest) -> Member:
    existing_member = repository.find_by_email(db, request.email)

    if existing_member is not None:
        raise MemberAlreadyExists(request.email)

    member = Member(
        name=request.name,
        email=request.email,
        # TEMP
        password_hash = password_hasher.hash("password")
    )

    repository.save(db, member)

    db.commit()
    db.refresh(member)

    return member


def update_member(db: Session, member_id: int, request: UpdateMemberRequest) -> Member:
    member = get_member(db, member_id)

    if request.name is not None:
        member.name = request.name

    db.commit()
    db.refresh(member)

    return member


def delete_member(db: Session, member_id: int) -> None:
    member = get_member(db, member_id)

    repository.delete(db, member)

    db.commit()

# app/domain/member/service.py

def _get_member_or_throw(db: Session, member_id: int) -> Member:
    member = repository.find_by_id(db, member_id)

    if member is None:
        raise MemberNotFound(member_id)

    return member