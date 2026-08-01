from fastapi import status

from app.core.exceptions import AppException


class MemberNotFound(AppException):

    def __init__(self, member_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
            member_id=member_id
        )


class MemberAlreadyExists(AppException):

    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member already exists",
            email=email
        )