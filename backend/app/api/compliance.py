import os
from tempfile import template

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.database.db import get_db

from app.services.document_parser import (
    DocumentParser
)

from app.services.report_extractor import (
    ReportExtractor
)

from app.services.compliance_engine import (
    ComplianceEngine
)

from app.services.validation_result_service import (
    ValidationResultService
)

from app.services.report_extraction_service import (
    ReportExtractionService
)

from app.services.template_service import (
    TemplateService
)

from app.services.report_service import (
    ReportService
)

from app.models.report_version import (
    ReportVersion
)

from app.models.report import Report

from app.models.template import Template

router = APIRouter(
    prefix="/compliance",
    tags=["Compliance"]
)


@router.post("/validate")
def validate_report(
    filename: str,
    report_version_id: int,
    db: Session = Depends(get_db)
):

    file_path = os.path.join(
        "uploads",
        filename
    )

    if not os.path.exists(file_path):

        return {
            "status": "error",
            "message": "File not found"
        }

    # Parse Document

    if file_path.endswith(".pdf"):

        parsed = DocumentParser.parse_pdf(
            file_path
        )

    elif file_path.endswith(".docx"):

        parsed = DocumentParser.parse_docx(
            file_path
        )

    else:

        return {
            "status": "error",
            "message":
                "Unsupported file type"
        }

    # Extract Data

    # Validate Report Version

    report_version = (
        db.query(ReportVersion)
        .filter(
            ReportVersion.id
            ==
            report_version_id
        )
        .first()
    )

    if not report_version:

        return {
            "status": "error",
            "message":
                "Report Version Not Found"
        }

    # Validate Report

    report = (
        db.query(Report)
        .filter(
            Report.id
            ==
            report_version.report_id
        )
        .first()
    )

    if not report:

        return {
            "status": "error",
            "message":
                "Report Not Found"
        }

    # Validate Template

    template = (
        db.query(Template)
        .filter(
            Template.id
            ==
            report.template_id
        )
        .first()
    )

    if not template:

        return {
            "status": "error",
            "message":
                "Template Not Found"
        }

# Extract Data

    extracted = ReportExtractor.extract(
        parsed,
        template.schema_json
    )
    
    # Store Extraction

    ReportExtractionService.create_or_update(
        db=db,
        report_version_id=report_version_id,
        extracted_json=extracted
    )

    # Latest Template Check

    latest_template = (
        TemplateService
        .get_latest_template(db)
    )

    latest_template_check = (
        latest_template.id
        ==
        template.id
    )

    # Compliance Validation

    validation = (
        ComplianceEngine.validate(
            extracted,
            template.schema_json,
            latest_template_check
        )
    )

    # Store Validation Result

    ValidationResultService.create_validation_result(
        db=db,
        report_version_id=report_version_id,
        compliance_score=validation[
            "compliance_score"
        ],
        issues=validation[
            "issues"
        ]
    )

    # Update Report Status

    if validation["status"] == "passed":

        ReportService.update_status(
            db,
            report.id,
            "validation_passed"
        )

    else:

        ReportService.update_status(
            db,
            report.id,
            "validation_failed"
        )

    return {

        "file_path":
            file_path,

        "extracted_data":
            extracted,

        "validation_result":
            validation
    }