from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


class AssignMembershipRequest(BaseModel):
    user_id: int
    club_id: int
    role: UserRole


class BulkAssignMembershipRequest(BaseModel):
    user_id: int
    club_ids: list[int]
    role: UserRole


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    is_active: bool

    created_by: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True
