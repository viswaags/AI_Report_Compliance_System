import json
import os

from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()


class GoogleDriveService:

    @classmethod
    def get_service(cls):

        try:
            token_json = os.getenv("GOOGLE_TOKEN_JSON")

            if token_json and token_json.strip():
                credentials = Credentials.from_authorized_user_info(
                    json.loads(token_json)
                )
            else:
                token_file = os.getenv("GOOGLE_OAUTH_TOKEN")

                credentials = Credentials.from_authorized_user_file(
                    token_file
                )

            return build(
                "drive",
                "v3",
                credentials=credentials
            )

        except json.JSONDecodeError as e:
            raise RuntimeError(
                "GOOGLE_TOKEN_JSON contains invalid JSON."
            ) from e

        except FileNotFoundError as e:
            raise RuntimeError(
                "Google OAuth token file not found."
            ) from e

        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Google Drive service: {e}"
            ) from e

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