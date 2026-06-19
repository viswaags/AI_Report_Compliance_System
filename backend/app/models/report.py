from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime
)
from sqlalchemy.sql import func

from app.database.db import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(
        Integer,
        primary_key=True
    )

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False
    )

    template_id = Column(
        Integer,
        ForeignKey("templates.id"),
        nullable=False
    )

    status = Column(
    String,
    default="draft"
    )

    current_version = Column(
        Integer,
        default=1
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )