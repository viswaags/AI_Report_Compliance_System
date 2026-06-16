from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db

from app.models.report import Report
from app.models.report_version import ReportVersion

from app.schemas.report import ReportCreate

import os

from fastapi import UploadFile
from fastapi import File
from fastapi import Form

from app.models.template import Template

from app.services.document_parser import DocumentParser
from app.services.report_extractor import ReportExtractor
from app.services.compliance_engine import ComplianceEngine

from app.services.report_extraction_service import (
    ReportExtractionService
)

from app.services.validation_result_service import (
    ValidationResultService
)

from app.services.template_service import (
    TemplateService
)

from app.services.report_service import (
    ReportService
)

from app.services.report_version_service import (
    ReportVersionService
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@router.post("/")
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db)
):

    db_report = Report(
        event_id=report.event_id,
        template_id=report.template_id
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

    return db.query(
        Report
    ).all()

@router.post("/submit")
def submit_report(
    event_id: int = Form(...),
    template_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(
        upload_dir,
        file.filename
    )

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    #
    # Create Report
    #

    report = Report(
        event_id=event_id,
        template_id=template_id,
        status="VALIDATING",
        current_version=1
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    #
    # Create Version
    #

    version = ReportVersion(
    report_id=report.id,
    version_no=1,
    drive_file_id=None,
    file_path=file_path
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    #
    # Parse File
    #

    if file.filename.endswith(".pdf"):

        parsed = DocumentParser.parse_pdf(
            file_path
        )

    elif file.filename.endswith(".docx"):

        parsed = DocumentParser.parse_docx(
            file_path
        )

    else:

        return {
            "status": "error",
            "message": "Unsupported file type"
        }

    #
    # Template
    #

    template = (
        db.query(Template)
        .filter(
            Template.id == template_id
        )
        .first()
    )

    if not template:

        return {
            "status": "error",
            "message": "Template not found"
        }

    #
    # Extract
    #

    extracted = ReportExtractor.extract(
        parsed,
        template.schema_json
    )

    ReportExtractionService.create_or_update(
        db=db,
        report_version_id=version.id,
        extracted_json=extracted
    )

    #
    # Validate
    #

    latest_template = (
        TemplateService.get_latest_template(db)
    )

    latest_template_check = (
        latest_template.id ==
        template.id
    )

    validation = (
        ComplianceEngine.validate(
            extracted,
            template.schema_json,
            latest_template_check
        )
    )

    ValidationResultService.create_validation_result(
        db=db,
        report_version_id=version.id,
        compliance_score=validation[
            "compliance_score"
        ],
        issues=validation[
            "issues"
        ]
    )

    #
    # Update Status
    #

    if validation["status"] == "passed":

        ReportService.update_status(
            db,
            report.id,
            "COMPLIANCE_PASSED"
        )

    else:

        ReportService.update_status(
            db,
            report.id,
            "CORRECTION_REQUIRED"
        )

    return {
        "report_id": report.id,
        "version_id": version.id,
        "validation": validation
    }

@router.post("/resubmit")
def resubmit_report(
    report_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    report = ReportService.get_report(
        db,
        report_id
    )

    if not report:

        return {
            "status": "error",
            "message": "Report not found"
        }

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    next_version = (
        ReportService.increment_version(
            db,
            report_id
        )
    )

    filename = (
        f"report_{report_id}_v"
        f"{next_version}_"
        f"{file.filename}"
    )

    file_path = os.path.join(
        upload_dir,
        filename
    )

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    version = (
        ReportVersionService.create_version(
            db=db,
            report_id=report_id,
            version_no=next_version,
            file_path=file_path
        )
    )

    #
    # Parse
    #

    if file.filename.endswith(".pdf"):

        parsed = DocumentParser.parse_pdf(
            file_path
        )

    elif file.filename.endswith(".docx"):

        parsed = DocumentParser.parse_docx(
            file_path
        )

    else:

        return {
            "status": "error",
            "message": "Unsupported file type"
        }

    #
    # Template
    #

    template = (
        db.query(Template)
        .filter(
            Template.id ==
            report.template_id
        )
        .first()
    )

    if not template:

        return {
            "status": "error",
            "message": "Template not found"
        }

    #
    # Extract
    #

    extracted = ReportExtractor.extract(
        parsed,
        template.schema_json
    )

    ReportExtractionService.create_or_update(
        db=db,
        report_version_id=version.id,
        extracted_json=extracted
    )

    #
    # Validate
    #

    latest_template = (
        TemplateService.get_latest_template(db)
    )

    latest_template_check = (
        latest_template.id ==
        template.id
    )

    validation = (
        ComplianceEngine.validate(
            extracted,
            template.schema_json,
            latest_template_check
        )
    )

    ValidationResultService.create_validation_result(
        db=db,
        report_version_id=version.id,
        compliance_score=validation[
            "compliance_score"
        ],
        issues=validation[
            "issues"
        ]
    )

    #
    # Status Update
    #

    if validation["status"] == "passed":

        ReportService.update_status(
            db,
            report.id,
            "COMPLIANCE_PASSED"
        )

    else:

        ReportService.update_status(
            db,
            report.id,
            "CORRECTION_REQUIRED"
        )

    return {
        "report_id": report.id,
        "version_no": next_version,
        "report_version_id": version.id,
        "validation": validation
    }

@router.get("/{report_id}/history")
def report_history(
    report_id: int,
    db: Session = Depends(get_db)
):

    versions = (
        db.query(
            ReportVersion
        )
        .filter(
            ReportVersion.report_id
            ==
            report_id
        )
        .order_by(
            ReportVersion.version_no
        )
        .all()
    )

    return versions

@router.get("/{report_id}")
def get_report_details(
    report_id: int,
    db: Session = Depends(get_db)
):

    report = (
        db.query(Report)
        .filter(
            Report.id == report_id
        )
        .first()
    )

    if not report:

        return {
            "status": "error",
            "message": "Report not found"
        }

    versions = (
        db.query(
            ReportVersion
        )
        .filter(
            ReportVersion.report_id
            ==
            report_id
        )
        .all()
    )

    return {
        "report": report,
        "versions": versions
    }