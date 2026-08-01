from pydantic import BaseModel, EmailStr, ConfigDict


class CreateMemberRequest(BaseModel):
    name: str
    email: EmailStr


class UpdateMemberRequest(BaseModel):
    name: str | None = None


class MemberResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)