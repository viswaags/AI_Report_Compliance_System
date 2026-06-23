from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime
)

from sqlalchemy.sql import func

from app.database.db import Base

from sqlalchemy import UniqueConstraint


class Event(Base):
    __tablename__ = "events"

    id = Column(
        Integer,
        primary_key=True
    )

    club_id = Column(
        Integer,
        ForeignKey("clubs.id"),
        nullable=False
    )

    event_title = Column(
        String,
        nullable=False
    )

    event_category = Column(
        String
    )

    event_date = Column(
        String
    )

    status = Column(
        String,
        default="created"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "club_id",
            "event_title",
            "event_date",
            name="uq_event"
        ),
    )