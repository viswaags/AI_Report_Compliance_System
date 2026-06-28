from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class MembershipUserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class MembershipClubResponse(BaseModel):
    id: int
    club_name: str

    class Config:
        from_attributes = True


class ClubMembershipResponse(BaseModel):
    id: int
    user_id: int
    club_id: int
    role: UserRole
    is_active: bool
    created_at: datetime | None = None

    user: MembershipUserResponse
    club: MembershipClubResponse

    class Config:
        from_attributes = True