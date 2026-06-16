import os
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.dependencies import get_db
from app.models.template import Template
from app.models.user import User, UserRole
from app.schemas.template import (
    TemplateAnalyzeResponse,
    TemplateCreate,
    TemplateResponse,
)
from app.services.template_analyzer import TemplateAnalyzer
from app.services.template_service import TemplateService


router = APIRouter(
    prefix="/templates",
    tags=["Templates"]
)

TEMPLATE_UPLOAD_DIR = "uploads/templates"

os.makedirs(TEMPLATE_UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=TemplateResponse)
def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    return TemplateService.create_template(
        db=db,
        version=template.version,
        schema_json=template.template_schema
    )


@router.post("/upload", response_model=TemplateResponse)
async def upload_template(
    version: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    extension = os.path.splitext(file.filename or "")[1].lower()

    if extension not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX templates are supported"
        )

    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(TEMPLATE_UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as template_file:
        shutil.copyfileobj(file.file, template_file)

    schema_json = TemplateAnalyzer.analyze_file(
        file_path=file_path,
        version=version
    )

    return TemplateService.create_template(
        db=db,
        version=version,
        schema_json=schema_json
    )


@router.post("/analyze", response_model=TemplateAnalyzeResponse)
async def analyze_template(
    version: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    extension = os.path.splitext(file.filename or "")[1].lower()

    if extension not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX templates are supported"
        )

    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(TEMPLATE_UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as template_file:
        shutil.copyfileobj(file.file, template_file)

    schema_json = TemplateAnalyzer.analyze_file(
        file_path=file_path,
        version=version
    )

    return TemplateAnalyzeResponse(
        version=version,
        schema_json=schema_json
    )


@router.get("/", response_model=list[TemplateResponse])
def get_templates(
    db: Session = Depends(get_db)
):
    return db.query(Template).all()
