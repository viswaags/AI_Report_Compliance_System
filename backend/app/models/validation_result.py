from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database.db import Base


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True)

    report_version_id = Column(
        Integer,
        ForeignKey("report_versions.id")
    )

    issues_json = Column(JSONB)

    compliance_score = Column(Float)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )