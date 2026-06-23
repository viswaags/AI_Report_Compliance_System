from fastapi import APIRouter

from app.services.document_parser import DocumentParser
from app.services.report_extractor import ReportExtractor
from app.services.compliance_engine import ComplianceEngine
from fastapi import Depends

from app.auth.dependencies import (
    require_role
)

from app.models.user import (
    User,
    UserRole
)

router = APIRouter(
    prefix="/parser",
    tags=["Parser"]
)


@router.get("/pdf")
def parse_pdf(
    path: str,
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):
    return DocumentParser.parse_pdf(path)


@router.get("/docx")
def parse_docx(
    path: str,
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):
    return DocumentParser.parse_docx(path)

@router.get("/extract-pdf")
def extract_pdf(
    path: str,
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):

    parsed = DocumentParser.parse_pdf(path)

    extracted = ReportExtractor.extract(
        parsed["text"]
    )

    return extracted

@router.get("/validate-pdf")
def validate_pdf(
    path: str,
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):

    parsed = DocumentParser.parse_pdf(path)

    extracted = ReportExtractor.extract(
        parsed["text"]
    )

    result = ComplianceEngine.validate(
        extracted
    )

    return {
        "extracted_data": extracted,
        "validation_result": result
    }