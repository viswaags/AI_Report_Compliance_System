import os

from fastapi import APIRouter, UploadFile, File

from fastapi import Depends

from app.auth.dependencies import (
    require_role
)

from app.models.user import (
    User,
    UserRole
)

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_report(
    file: UploadFile = File(...),

    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):
    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {
        "filename": file.filename,
        "saved_to": file_path
    }