from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.dependencies import get_db
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.review import ReviewCreate
from app.services.review_service import ReviewService
from app.services.access_control_service import AccessControlService
from app.schemas.review_action import ReviewActionRequest

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

    user_role = (
        current_user.role.value
        if isinstance(current_user.role, UserRole)
        else current_user.role
    )

    if user_role != UserRole.ADMIN.value:

        if not AccessControlService.user_can_access_report(
            db,
            current_user.id,
            review.report_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to review this report"
            )

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

@router.get("/pending")
def pending_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR
        ])
    )
):
    from app.models.report import Report

    return (
        db.query(Report)
        .filter(
            Report.status == "COMPLIANCE_PASSED"
        )
        .all()
    )

@router.get("/report/{report_id}")
def review_report_details(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR
        ])
    )
):
    from app.models.report_extraction import ReportExtraction
    from app.models.report_version import ReportVersion
    from app.models.validation_result import ValidationResult

    version = (
        db.query(ReportVersion)
        .filter(
            ReportVersion.report_id == report_id
        )
        .order_by(
            ReportVersion.version_no.desc()
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Report version not found"
        )

    extraction = (
        db.query(ReportExtraction)
        .filter(
            ReportExtraction.report_version_id == version.id
        )
        .first()
    )

    validation = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.report_version_id == version.id
        )
        .order_by(
            ValidationResult.id.desc()
        )
        .first()
    )

    return {
        "report_id": report_id,
        "version": version,
        "extraction":
            extraction.extracted_json if extraction else None,
        "validation": validation
    }

@router.post("/approve")
def approve_report(
    request: ReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR
        ])
    )
):
    return ReviewService.create_review(
        db=db,
        report_id=request.report_id,
        reviewer_id=current_user.id,
        status="APPROVED",
        comments=request.comments
    )

@router.post("/reject")
def reject_report(
    request: ReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR
        ])
    )
):
    return ReviewService.create_review(
        db=db,
        report_id=request.report_id,
        reviewer_id=current_user.id,
        status="REJECTED",
        comments=request.comments
    )