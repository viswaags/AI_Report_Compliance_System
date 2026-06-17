import os

from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


load_dotenv()


class GoogleDriveService:

    TOKEN_FILE = os.getenv(
        "GOOGLE_OAUTH_TOKEN"
    )

    @classmethod
    def get_service(cls):

        credentials = Credentials.from_authorized_user_file(
            cls.TOKEN_FILE
        )

        return build(
            "drive",
            "v3",
            credentials=credentials
        )

    @classmethod
    def upload_file(
        cls,
        file_path: str,
        folder_id: str | None = None
    ):

        service = cls.get_service()

        metadata = {
            "name": os.path.basename(file_path)
        }

        if folder_id:
            metadata["parents"] = [folder_id]

        media = MediaFileUpload(
            file_path,
            resumable=True
        )

        uploaded_file = (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id,name"
            )
            .execute()
        )

        return uploaded_file["id"]

    @classmethod
    def get_file_url(
        cls,
        drive_file_id: str
    ):

        return (
            f"https://drive.google.com/file/d/"
            f"{drive_file_id}/view"
        )