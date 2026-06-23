from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.database.db import Base


class ReportVersion(Base):
    __tablename__ = "report_versions"

    id = Column(Integer, primary_key=True)

    report_id = Column(
        Integer,
        ForeignKey("reports.id")
    )

    version_no = Column(Integer)

    template_id = Column(
        Integer,
        ForeignKey("templates.id"),
        nullable=False
    )

    drive_file_id = Column(String)

    file_path = Column(String)

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )