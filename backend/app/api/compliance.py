import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.models.report import Report
from app.models.report_version import ReportVersion
from app.services.report_pipeline_service import ReportPipelineService
from app.auth.dependencies import require_role
from app.models.user import User
from app.models.user import UserRole
from app.services.access_control_service import (
    AccessControlService
)

router = APIRouter(
    prefix="/compliance",
    tags=["Compliance"]
)


@router.post("/validate")
def validate_report(
    filename: str,
    report_version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR,
            UserRole.STUDENT_REPRESENTATIVE
        ])
    )
):
    report_version = (
        db.query(ReportVersion)
        .filter(ReportVersion.id == report_version_id)
        .first()
    )
    if not report_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report version not found"
        )

    report = (
        db.query(Report)
        .filter(Report.id == report_version.report_id)
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if current_user.role != UserRole.ADMIN:

        if not AccessControlService.user_can_access_report(
            db,
            current_user.id,
            report.id
        ):
            raise HTTPException(
                status_code=403,
                detail="No access to this report"
            )

    file_path = report_version.file_path or os.path.join("uploads", filename)
    if not os.path.exists(file_path):
        file_path = os.path.join("uploads", filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    try:
        pipeline_result = ReportPipelineService.process_report_version(
            db,
            report,
            report_version,
            file_path
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

    return {
        "file_path": file_path,
        "raw_extraction": pipeline_result["raw_extraction"],
        "canonical_report_model": pipeline_result["canonical_report_model"],
        "validation_result": pipeline_result["validation"],
        "validation_result_id": pipeline_result["validation_result"].id
    }
