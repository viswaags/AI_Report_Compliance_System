from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database.db import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    version = Column(String, nullable=False)
    schema_json = Column(JSONB, nullable=False)
    drive_file_id = Column(String)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )