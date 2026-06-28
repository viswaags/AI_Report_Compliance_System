from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.feedback import FeedbackBundleResponse
from app.services.feedback_service import FeedbackService


router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"]
)


@router.post("/generate/{validation_result_id}")
def generate_feedback(
    validation_result_id: int,
    db: Session = Depends(get_db)
):
    try:
        feedback =  FeedbackService.generate_feedback(
            db,
            validation_result_id
        )

        db.commit()

        return feedback
    
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc


@router.post("/{validation_result_id}", response_model=FeedbackBundleResponse)
def generate_feedback_bundle(
    validation_result_id: int,
    db: Session = Depends(get_db)
):
    try:
        feedback =  FeedbackService.generate_feedback_bundle(
            db,
            validation_result_id
        )

        db.commit()

        return feedback 
    
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc
