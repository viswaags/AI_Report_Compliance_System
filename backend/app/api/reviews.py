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
from app.models.report_extraction import ReportExtraction
from app.models.report_version import ReportVersion
from app.models.validation_result import ValidationResult
from app.services.review_workflow_runner_service import ReviewWorkflowRunnerService
from app.auth.dependencies import get_current_user
from app.models.report import Report

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
        review =  ReviewService.create_review(
            db=db,
            report_id=review.report_id,
            reviewer_id=reviewer_id,
            status=review.status,
            comments=review.comments
        )

        db.commit()

        return review

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc


@router.get("/")
def get_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR,
            UserRole.FACULTY_REPRESENTATIVE,
            UserRole.STUDENT_REPRESENTATIVE
        ])
    )
):

    from app.models.report import Report
    from app.models.event import Event

    if current_user.role == UserRole.ADMIN:

        return (
            db.query(Review)
            .all()
        )

    club_ids = (
        AccessControlService
        .get_accessible_club_ids(
            db,
            current_user.id
        )
    )

    return (
        db.query(Review)
        .join(
            Report,
            Review.report_id == Report.id
        )
        .join(
            Event,
            Report.event_id == Event.id
        )
        .filter(
            Event.club_id.in_(club_ids)
        )
        .all()
    )

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
    from app.models.event import Event
    from app.models.report_version import ReportVersion

    from app.services.google_drive_service import (
        GoogleDriveService
    )

    if current_user.role == UserRole.ADMIN:

        reports = (
            db.query(Report)
            .filter(
                Report.status == "COMPLIANCE_PASSED"
            )
            .all()
        )

    else:

        club_ids = (
            AccessControlService
            .get_accessible_club_ids(
                db,
                current_user.id
            )
        )

        reports = (
            db.query(Report)
            .join(
                Event,
                Report.event_id == Event.id
            )
            .filter(
                Report.status == "COMPLIANCE_PASSED",
                Event.club_id.in_(club_ids)
            )
            .all()
        )

    response = []

    for report in reports:

        event = (
            db.query(Event)
            .filter(
                Event.id == report.event_id
            )
            .first()
        )

        latest_version = (
            db.query(ReportVersion)
            .filter(
                ReportVersion.report_id == report.id
            )
            .order_by(
                ReportVersion.version_no.desc()
            )
            .first()
        )

        drive_url = None

        if (
            latest_version
            and latest_version.drive_file_id
        ):
            drive_url = (
                GoogleDriveService
                .get_file_url(
                    latest_version.drive_file_id
                )
            )

        response.append(
            {
                "report_id": report.id,

                "event_title":
                    event.event_title
                    if event else None,

                "event_date":
                    event.event_date
                    if event else None,

                "club_id":
                    event.club_id
                    if event else None,

                "current_version":
                    latest_version.version_no
                    if latest_version else None,

                "status":
                    report.status,

                "drive_url":
                    drive_url
            }
        )

    return response

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
    from app.services.google_drive_service import (
        GoogleDriveService
    )

    if current_user.role != UserRole.ADMIN:

        if not AccessControlService.user_can_access_report(
            db,
            current_user.id,
            report_id
        ):
            raise HTTPException(
                status_code=403,
                detail="No access to this report"
            )

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

    drive_url = None

    if version.drive_file_id:

        drive_url = (
            GoogleDriveService
            .get_file_url(
                version.drive_file_id
            )
        )

    return {
        "report_id": report_id,

        "drive_file_id":
            version.drive_file_id,

        "drive_url":
            drive_url,

        "version":
            version,

        "extraction":
            extraction.extracted_json
            if extraction else None,

        "validation":
            validation
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

    if current_user.role != UserRole.ADMIN:

        if not AccessControlService.user_can_access_report(
            db,
            current_user.id,
            request.report_id
        ):
            raise HTTPException(
                status_code=403,
                detail="No access to this report"
            )

    workflow_result = ReviewWorkflowRunnerService.run(
        db=db,
        report_id=request.report_id,
        reviewer_id=current_user.id,
        review_status="APPROVED",
        comments=request.comments
    )

    return workflow_result["review"]

    '''
    return ReviewService.create_review(
        db=db,
        report_id=request.report_id,
        reviewer_id=current_user.id,
        status="APPROVED",
        comments=request.comments
    )'''

@router.post("/revision-required")
def request_revision(
    request: ReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR
        ])
    )
):

    if current_user.role != UserRole.ADMIN:

        if not AccessControlService.user_can_access_report(
            db,
            current_user.id,
            request.report_id
        ):
            raise HTTPException(
                status_code=403,
                detail="No access to this report"
            )
        
    workflow_result = ReviewWorkflowRunnerService.run(
        db=db,
        report_id=request.report_id,
        reviewer_id=current_user.id,
        review_status="REVISION_REQUIRED",
        comments=request.comments
    )

    return workflow_result["review"]

    '''
    return ReviewService.create_review(
        db=db,
        report_id=request.report_id,
        reviewer_id=current_user.id,
        status="REVISION_REQUIRED",
        comments=request.comments
    )'''

@router.get("/stats")
def review_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR
        ])
    )
):

    pending = (
        db.query(Report)
        .filter(
            Report.status ==
            "COMPLIANCE_PASSED"
        )
        .count()
    )

    approved = (
        db.query(Report)
        .filter(
            Report.status ==
            "APPROVED"
        )
        .count()
    )

    revision_required = (
        db.query(Report)
        .filter(
            Report.status ==
            "REVISION_REQUIRED"
        )
        .count()
    )

    return {
        "pending_reviews":
            pending,

        "approved":
            approved,

        "revision_required":
            revision_required
    }

@router.get("/report/{report_id}/history")
def review_history(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        db.query(Review)
        .join(
            ReportVersion,
            Review.report_version_id ==
            ReportVersion.id
        )
        .filter(
            ReportVersion.report_id ==
            report_id
        )
        .order_by(
            Review.id.desc()
        )
        .all()
    )

@router.get("/report/{report_id}/latest")
def latest_review(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    review = (
        db.query(Review)
        .join(
            ReportVersion,
            Review.report_version_id ==
            ReportVersion.id
        )
        .filter(
            ReportVersion.report_id ==
            report_id
        )
        .order_by(
            Review.id.desc()
        )
        .first()
    )

    return review