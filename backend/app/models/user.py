import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, DateTime, func

from app.database.db import Base

from sqlalchemy.orm import relationship


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    CLUB_COORDINATOR = "CLUB_COORDINATOR"
    FACULTY_REPRESENTATIVE = "FACULTY_REPRESENTATIVE"
    STUDENT_REPRESENTATIVE = "STUDENT_REPRESENTATIVE"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )
    creator = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[created_by],
        backref="created_users"
    )
    must_change_password = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

