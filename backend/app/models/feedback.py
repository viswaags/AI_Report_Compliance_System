from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    ForeignKey,
    DateTime
)

from sqlalchemy.sql import func

from app.database.db import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(
        Integer,
        primary_key=True
    )

    validation_result_id = Column(
        Integer,
        ForeignKey("validation_results.id"),
        nullable=False
    )

    feedback_text = Column(
        Text,
        nullable=False
    )

    model_used = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )