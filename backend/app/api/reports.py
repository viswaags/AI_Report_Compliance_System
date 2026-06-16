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

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


UPLOAD_DIR = "uploads"


@router.post("/")
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db)
):
    db_report = Report(
        event_id=report.event_id,
        template_id=report.template_id,
        current_version=1
    )

    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    db_version = ReportVersion(
        report_id=db_report.id,
        version_no=1,
        drive_file_id=None
    )

    db.add(db_version)
    db.commit()
    db.refresh(db_version)

    return {
        "report": db_report,
        "version": db_version
    }


@router.get("/")
def get_reports(
    db: Session = Depends(get_db)
):
    return db.query(Report).all()


@router.post("/submit")
def submit_report(
    event_id: int = Form(...),
    template_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.STUDENT_REPRESENTATIVE
        )
    )
):
    file_path = _save_upload(file)

    report = Report(
        event_id=event_id,
        template_id=template_id,
        status="VALIDATING",
        current_version=1
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    version = ReportVersion(
        report_id=report.id,
        version_no=1,
        drive_file_id=None,
        file_path=file_path
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    try:
        pipeline_result = ReportPipelineService.process_report_version(
            db,
            report,
            version,
            file_path
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

    return {
        "report_id": report.id,
        "version_id": version.id,
        "raw_extraction": pipeline_result["raw_extraction"],
        "canonical_report_model": pipeline_result["canonical_report_model"],
        "validation": pipeline_result["validation"],
        "validation_result_id": pipeline_result["validation_result"].id
    }


@router.post("/resubmit")
def resubmit_report(
    report_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.STUDENT_REPRESENTATIVE
        )
    )
):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    next_version = ReportService.increment_version(db, report_id)
    filename = f"report_{report_id}_v{next_version}_{file.filename}"
    file_path = _save_upload(file, filename)

    version = ReportVersionService.create_version(
        db=db,
        report_id=report_id,
        version_no=next_version,
        file_path=file_path
    )

    try:
        pipeline_result = ReportPipelineService.process_report_version(
            db,
            report,
            version,
            file_path
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

    return {
        "report_id": report.id,
        "version_no": next_version,
        "report_version_id": version.id,
        "raw_extraction": pipeline_result["raw_extraction"],
        "canonical_report_model": pipeline_result["canonical_report_model"],
        "validation": pipeline_result["validation"],
        "validation_result_id": pipeline_result["validation_result"].id
    }


@router.get("/{report_id}/compliance")
def get_report_compliance(
    report_id: int,
    db: Session = Depends(get_db)
):
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
    db: Session = Depends(get_db)
):
    feedback = FeedbackService.latest_feedback_for_report(db, report_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    return feedback


@router.get("/{report_id}/email-draft")
def get_report_email_draft(
    report_id: int,
    db: Session = Depends(get_db)
):
    draft = FeedbackService.latest_email_draft_for_report(db, report_id)
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email draft not found"
        )

    return draft


@router.get("/{report_id}/history")
def report_history(
    report_id: int,
    db: Session = Depends(get_db)
):
    versions = (
        db.query(ReportVersion)
        .filter(ReportVersion.report_id == report_id)
        .order_by(ReportVersion.version_no)
        .all()
    )

    history = []
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
        history.append({
            "version": version,
            "extraction": extraction.extracted_json if extraction else None,
            "validation": validation
        })

    return history


@router.get("/{report_id}")
def get_report_details(
    report_id: int,
    db: Session = Depends(get_db)
):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
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
