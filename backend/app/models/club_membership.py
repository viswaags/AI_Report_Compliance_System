from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.sql import func

from app.database.db import Base
from app.models.user import UserRole


class ClubMembership(Base):
    __tablename__ = "club_memberships"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    club_id = Column(
        Integer,
        ForeignKey("clubs.id"),
        nullable=False
    )

    role = Column(
        Enum(UserRole),
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "club_id", name="uq_club_memberships_user_club"),
    )
