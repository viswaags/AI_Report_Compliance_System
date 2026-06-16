from sqlalchemy import Column, Integer, String

from app.database.db import Base


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    club_name = Column(String, nullable=False)
    description = Column(String)