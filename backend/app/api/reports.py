import os
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.models.feedback import Feedback
from app.models.report import Report
from app.models.report_extraction import ReportExtraction
from app.models.report_version import ReportVersion
from app.models.validation_result import ValidationResult
from app.schemas.report import ReportCreate
from app.services.feedback_service import FeedbackService
from app.services.report_pipeline_service import ReportPipelineService
from app.services.report_service import ReportService
from app.services.report_version_service import ReportVersionService
from app.auth.dependencies import require_role
from app.models.user import User, UserRole
from app.auth.dependencies import get_current_user
from app.services.access_control_service import AccessControlService
from app.models.event import Event
from app.services.report_drive_service import (
    ReportDriveService
)
from app.services.template_service import TemplateService
from app.services.workflow_runner_service import (
    WorkflowRunnerService
)
from app.models.club_membership import (
    ClubMembership
)

from app.services.notification_service import (
    NotificationService
)

from app.services.template_version_service import (
    TemplateVersionService
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


UPLOAD_DIR = "uploads"

@router.post("/submit")
def submit_report(
    event_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.STUDENT_REPRESENTATIVE,
            UserRole.CLUB_COORDINATOR
        ])
    )
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    latest_template = (
        TemplateService.get_latest_template(db)
    )

    if not latest_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No template available"
        )

    user_role = (
        current_user.role.value
        if isinstance(current_user.role, UserRole)
        else current_user.role
    )

    if user_role != UserRole.ADMIN.value:

        if not AccessControlService.user_can_access_event(
            db,
            current_user.id,
            event_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this event"
            )

    file_path = _save_upload(file)

    report = Report(
        event_id=event_id,
        template_id=latest_template.id,
        status="VALIDATING",
        current_version=1,
        created_by=current_user.id
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    club_id = event.club_id

    memberships = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.club_id == event.club_id,
            ClubMembership.role ==
                UserRole.CLUB_COORDINATOR,
            ClubMembership.is_active == True
        )
        .all()
    )

    for membership in memberships:

        NotificationService.create_notification(
            db=db,
            user_id=membership.user_id,
            title="New Report Submitted",
            message=(
                f"Report #{report.id} "
                f"for event "
                f"'{event.event_title}' "
                f"has been submitted."
            ),
            notification_type="REPORT"
        )

    version = ReportVersion(
        report_id=report.id,
        version_no=1,
        template_id=latest_template.id,
        drive_file_id=None,
        file_path=file_path
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    ReportDriveService.upload_report_version(
        db=db,
        report=report,
        report_version=version,
        file_path=file_path
    )

    try:
        '''pipeline_result = ReportPipelineService.process_report_version(
            db,
            report,
            version,
            file_path
        )'''

        workflow_result = (
            WorkflowRunnerService
            .run_report_workflow(
                db=db,
                report=report,
                report_version=version,
                file_path=file_path
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

    '''return {
        "report_id": report.id,
        "version_id": version.id,
        "validation_result_id":
            pipeline_result["validation_result"].id,
        "validation":
            pipeline_result["validation"]
    }'''

    return {
        "report_id": report.id,
        "version_id": version.id,
        "validation_result_id":
            workflow_result[
                "validation_result"
            ].id,

        "validation":
            workflow_result[
                "validation"
            ]
    }

@router.post("/resubmit")
def resubmit_report(
    report_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.STUDENT_REPRESENTATIVE,
            UserRole.CLUB_COORDINATOR
        ])
    )
):
    report = ReportService.get_report(
        db,
        report_id
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.status == "APPROVED":
        raise HTTPException(
            status_code=400,
            detail="Approved reports cannot be resubmitted"
        )

    user_role = (
        current_user.role.value
        if isinstance(current_user.role, UserRole)
        else current_user.role
    )

    if user_role != UserRole.ADMIN.value:

        if not AccessControlService.user_can_access_report(
            db,
            current_user.id,
            report_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this report"
            )

    next_version = ReportService.increment_version(
        db,
        report_id
    )

    ReportService.update_status(
        db,
        report_id,
        "VALIDATING"
    )

    filename = (
        f"report_{report_id}_v{next_version}_{file.filename}"
    )

    file_path = _save_upload(
        file,
        filename
    )

    latest_template = (
        TemplateService.get_latest_template(db)
    )

    if not latest_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No template available"
        )

    version = ReportVersionService.create_version(
        db=db,
        report_id=report_id,
        version_no=next_version,
        template_id=latest_template.id,
        file_path=file_path
    )

    event = (
        db.query(Event)
        .filter(
            Event.id == report.event_id
        )
        .first()
    )

    memberships = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.club_id == event.club_id,
            ClubMembership.role ==
                UserRole.CLUB_COORDINATOR,
            ClubMembership.is_active == True
        )
        .all()
    )

    for membership in memberships:

        NotificationService.create_notification(
            db=db,
            user_id=membership.user_id,
            title="Report Resubmitted",
            message=(
                f"Report #{report.id} "
                f"has been resubmitted."
            ),
            notification_type="REPORT"
        )

    ReportDriveService.upload_report_version(
        db=db,
        report=report,
        report_version=version,
        file_path=file_path
    )

    try:
        '''pipeline_result = ReportPipelineService.process_report_version(
            db,
            report,
            version,
            file_path
        )'''

        workflow_result = (
            WorkflowRunnerService
            .run_report_workflow(
                db=db,
                report=report,
                report_version=version,
                file_path=file_path
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

    '''return {
        "report_id": report.id,
        "version_no": next_version,
        "report_version_id": version.id,
        "validation_result_id":
            pipeline_result["validation_result"].id,
        "validation":
            pipeline_result["validation"]
    }'''

    return {
        "report_id": report.id,
        "version_no": next_version,
        "report_version_id": version.id,

        "validation_result_id":
            workflow_result[
                "validation_result"
            ].id,

        "validation":
            workflow_result[
                "validation"
            ]
    }

@router.get("/")
def get_reports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    if current_user.role == UserRole.ADMIN:

        return (
            db.query(Report)
            .offset(skip)
            .limit(limit)
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
        db.query(Report)
        .join(
            Event,
            Report.event_id == Event.id
        )
        .filter(
            Event.club_id.in_(club_ids)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

@router.get("/my-reports")
def my_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    reports = (
        db.query(Report)
        .filter(
            Report.created_by ==
            current_user.id
        )
        .all()
    )

    result = []

    for report in reports:

        event = (
            db.query(Event)
            .filter(
                Event.id ==
                report.event_id
            )
            .first()
        )

        result.append(
            {
                "report_id": report.id,
                "event_title":
                    event.event_title
                    if event else None,
                "status":
                    report.status,
                "current_version":
                    report.current_version
            }
        )

    return result

@router.get("/{report_id}/status")
def report_status(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    report = (
        ReportService.get_report(
            db,
            report_id
        )
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
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

    return {
        "report_id":
            report.id,

        "status":
            report.status,

        "current_version":
            report.current_version
    }

@router.get("/{report_id}/summary")
def report_summary(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    report = (
        ReportService.get_report(
            db,
            report_id
        )
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
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

    event = (
        db.query(Event)
        .filter(
            Event.id ==
            report.event_id
        )
        .first()
    )

    return {

        "report_id":
            report.id,

        "event_id":
            report.event_id,

        "event_title":
            event.event_title
            if event else None,

        "event_category":
            event.event_category
            if event else None,

        "event_date":
            event.event_date
            if event else None,

        "status":
            report.status,

        "current_version":
            report.current_version,

        "template_id":
            report.template_id
    }

@router.get("/{report_id}/validation")
def latest_validation(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    report = (
        ReportService.get_report(
            db,
            report_id
        )
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
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

    validation = (
        _latest_validation(
            db,
            report_id
        )
    )

    if not validation:
        raise HTTPException(
            status_code=404,
            detail="Validation result not found"
        )

    return validation

@router.get("/{report_id}/latest-review")
def latest_review(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    report = (
        ReportService.get_report(
            db,
            report_id
        )
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
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

    from app.models.review import Review

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

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return review

@router.get("/{report_id}/template-status")
def report_template_status(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    report = ReportService.get_report(
        db,
        report_id
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return (
        TemplateVersionService
        .check_report_template_status(
            db,
            report
        )
    )

@router.get("/{report_id}/compliance")
def get_report_compliance(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):
    
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
        
    validation = _latest_validation(db, report_id)
    if not validation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance result not found"
        )

    return {
        "validation_result_id": validation.id,
        "report_version_id": validation.report_version_id,
        "compliance_score": validation.compliance_score,
        "issues_json": validation.issues_json,
        "created_at": validation.created_at
    }


@router.get("/{report_id}/feedback")
def get_report_feedback(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

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

    feedback = (
        FeedbackService
        .latest_feedback_for_report(
            db,
            report_id
        )
    )

    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found"
        )

    return feedback


@router.get("/{report_id}/email-draft")
def get_report_email_draft(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

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

    draft = (
        FeedbackService
        .latest_email_draft_for_report(
            db,
            report_id
        )
    )

    if not draft:
        raise HTTPException(
            status_code=404,
            detail="Email draft not found"
        )

    return draft


@router.get("/{report_id}/history")
def report_history(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):
    
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
        
    versions = (
        db.query(ReportVersion)
        .filter(ReportVersion.report_id == report_id)
        .order_by(ReportVersion.version_no)
        .all()
    )

    history = []
    from app.models.review import Review
    for version in versions:
        extraction = (
            db.query(ReportExtraction)
            .filter(ReportExtraction.report_version_id == version.id)
            .first()
        )
        validation = (
            db.query(ValidationResult)
            .filter(ValidationResult.report_version_id == version.id)
            .order_by(ValidationResult.id.desc())
            .first()
        )
        review = (
            db.query(Review)
            .filter(
                Review.report_version_id == version.id
            )
            .first()
        )

        feedback = None

        if validation:

            feedback = (
                db.query(Feedback)
                .filter(
                    Feedback.validation_result_id ==
                    validation.id
                )
                .order_by(
                    Feedback.id.desc()
                )
                .first()
            )

        history.append({
            "version": version,
            "extraction":
                extraction.extracted_json
                if extraction else None,

            "validation":
                validation,

            "feedback":
                feedback,

            "review":
                review
        })

    return history

@router.get("/{report_id}/versions")
def report_versions(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        db.query(
            ReportVersion
        )
        .filter(
            ReportVersion.report_id
            == report_id
        )
        .order_by(
            ReportVersion.version_no.desc()
        )
        .all()
    )

@router.get("/{report_id}")
def get_report_details(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
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

    versions = (
        db.query(ReportVersion)
        .filter(ReportVersion.report_id == report_id)
        .order_by(ReportVersion.version_no)
        .all()
    )

    return {
        "report": report,
        "versions": versions
    }


def _save_upload(file: UploadFile, filename: str | None = None):
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX reports are supported"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_filename = os.path.basename(filename or file.filename or "report")
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as output_file:
        shutil.copyfileobj(file.file, output_file)

    return file_path


def _latest_validation(db: Session, report_id: int):
    return (
        db.query(ValidationResult)
        .join(
            ReportVersion,
            ValidationResult.report_version_id == ReportVersion.id
        )
        .filter(ReportVersion.report_id == report_id)
        .order_by(ValidationResult.id.desc())
        .first()
    )