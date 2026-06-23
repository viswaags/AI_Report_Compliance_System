from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database.db import Base


class ReportExtraction(Base):

    __tablename__ = "report_extractions"

    id = Column(
        Integer,
        primary_key=True
    )

    report_version_id = Column(
        Integer,
        ForeignKey("report_versions.id"),
        unique=True
    )

    extracted_json = Column(
        JSONB,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )