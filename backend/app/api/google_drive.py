from fastapi import APIRouter

from app.services.google_drive_service import (
    GoogleDriveService
)

from app.services.google_drive_folder_service import (
    GoogleDriveFolderService
)

from fastapi import Depends

from app.auth.dependencies import (
    require_role
)

from app.models.user import (
    User,
    UserRole
)

router = APIRouter(
    prefix="/drive",
    tags=["Google Drive"]
)

@router.post("/initialize-repository")
def initialize_repository(
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):

    root = GoogleDriveFolderService.get_or_create_folder(
        "AI Report Compliance Repository"
    )

    templates = GoogleDriveFolderService.get_or_create_folder(
        "Templates",
        root["id"]
    )

    reports = GoogleDriveFolderService.get_or_create_folder(
        "Club Reports",
        root["id"]
    )

    return {
        "root": root,
        "templates": templates,
        "reports": reports
    }


@router.post("/test")
def upload_test(
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):

    file_id = (
        GoogleDriveService.upload_file(
            "uploads/Original_Report.pdf"
        )
    )

    return {
        "drive_file_id": file_id
    }