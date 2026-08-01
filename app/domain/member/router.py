from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.member import service
from app.domain.member.schema import CreateMemberRequest, MemberResponse, UpdateMemberRequest


router = APIRouter(
    prefix="/members",
    tags=["members"]
)


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)) -> MemberResponse:
    return service.get_member(db, member_id)


@router.get("", response_model=list[MemberResponse])
def get_members(db: Session = Depends(get_db)) -> list[MemberResponse]:
    return service.get_members(db)


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def create_member(request: CreateMemberRequest, db: Session = Depends(get_db)) -> MemberResponse:
    return service.create_member(db, request)


@router.patch("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, request: UpdateMemberRequest, db: Session = Depends(get_db)) -> MemberResponse:
    return service.update_member(db, member_id, request)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int, db: Session = Depends(get_db)) -> None:
    service.delete_member(db, member_id)