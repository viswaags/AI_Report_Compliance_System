from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.dependencies import get_db

from app.schemas.review import ReviewCreate

from app.services.review_service import (
    ReviewService
)

from app.services.report_service import (
    ReportService
)

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)


@router.post("/")
def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db)
):

    created_review = (
        ReviewService.create_review(
            db=db,
            report_id=review.report_id,
            reviewer_id=review.reviewer_id,
            status=review.status,
            comments=review.comments
        )
    )

    ReportService.update_status(
        db,
        review.report_id,
        review.status
    )

    return created_review

@router.get("/")
def get_reviews(
    db: Session = Depends(get_db)
):
    from app.models.review import Review

    return (
        db.query(Review)
        .all()
    )