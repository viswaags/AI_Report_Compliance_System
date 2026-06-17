from app.services.google_drive_service import (
    GoogleDriveService
)


class GoogleDriveFolderService:

    @staticmethod
    def find_folder(
        folder_name,
        parent_id=None
    ):

        service = GoogleDriveService.get_service()

        query = (
            f"name='{folder_name}' "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false"
        )

        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = (
            service.files()
            .list(
                q=query,
                fields="files(id,name)"
            )
            .execute()
        )

        folders = results.get(
            "files",
            []
        )

        if folders:
            return folders[0]

        return None

    @staticmethod
    def create_folder(
        folder_name,
        parent_id=None
    ):

        service = GoogleDriveService.get_service()

        metadata = {
            "name": folder_name,
            "mimeType":
                "application/vnd.google-apps.folder"
        }

        if parent_id:
            metadata["parents"] = [parent_id]

        return (
            service.files()
            .create(
                body=metadata,
                fields="id,name"
            )
            .execute()
        )

    @staticmethod
    def get_or_create_folder(
        folder_name,
        parent_id=None
    ):

        existing = (
            GoogleDriveFolderService.find_folder(
                folder_name,
                parent_id
            )
        )

        if existing:
            return existing

        return (
            GoogleDriveFolderService.create_folder(
                folder_name,
                parent_id
            )
        )