from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.dependencies import get_db

from app.services.feedback_service import (
    FeedbackService
)

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"]
)


@router.post(
    "/generate/{validation_result_id}"
)
def generate_feedback(

    validation_result_id: int,

    db: Session = Depends(
        get_db
    )
):

    feedback = (
        FeedbackService
        .generate_feedback(
            db,
            validation_result_id
        )
    )

    return feedback