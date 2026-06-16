from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.dependencies import get_db
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.review import ReviewCreate
from app.services.review_service import ReviewService


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)


@router.post("/")
def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.FACULTY_REPRESENTATIVE,
            UserRole.CLUB_COORDINATOR,
        ])
    )
):
    reviewer_id = current_user.id
    if review.reviewer_id != current_user.id:
        user_role = (
            current_user.role.value
            if isinstance(current_user.role, UserRole)
            else current_user.role
        )
        if user_role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Reviewer must match authenticated user"
            )
        reviewer_id = review.reviewer_id

    try:
        return ReviewService.create_review(
            db=db,
            report_id=review.report_id,
            reviewer_id=reviewer_id,
            status=review.status,
            comments=review.comments
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc


@router.get("/")
def get_reviews(
    db: Session = Depends(get_db)
):
    return db.query(Review).all()
