from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime
)

from sqlalchemy.sql import func

from app.database.db import Base


class EventRecord(Base):

    __tablename__ = "event_records"

    id = Column(
        Integer,
        primary_key=True
    )

    club_id = Column(
        Integer,
        ForeignKey("clubs.id"),
        nullable=False
    )

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False
    )

    report_id = Column(
        Integer,
        ForeignKey("reports.id"),
        nullable=False,
        unique=True
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

    coordinators_organizers = Column(String)

    venue = Column(String)

    participant_count = Column(
        Integer
    )

    approved_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    approved_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )