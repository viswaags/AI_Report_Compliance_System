from app.models.club import Club
from app.models.event import Event

from app.services.google_drive_service import (
    GoogleDriveService
)

from app.services.google_drive_folder_service import (
    GoogleDriveFolderService
)


class ReportDriveService:

    @staticmethod
    def upload_report_version(
        db,
        report,
        report_version,
        file_path
    ):

        event = (
            db.query(Event)
            .filter(
                Event.id == report.event_id
            )
            .first()
        )

        if not event:
            raise ValueError("Event not found")

        club = (
            db.query(Club)
            .filter(
                Club.id == event.club_id
            )
            .first()
        )

        if not club:
            raise ValueError("Club not found")

        root_folder = (
            GoogleDriveFolderService
            .get_or_create_folder(
                "AI Report Compliance Repository"
            )
        )

        reports_folder = (
            GoogleDriveFolderService
            .get_or_create_folder(
                "Club Reports",
                root_folder["id"]
            )
        )

        club_folder = (
            GoogleDriveFolderService
            .get_or_create_folder(
                club.club_name,
                reports_folder["id"]
            )
        )

        event_folder = (
            GoogleDriveFolderService
            .get_or_create_folder(
                event.event_title,
                club_folder["id"]
            )
        )

        drive_file_id = (
            GoogleDriveService.upload_file(
                file_path=file_path,
                folder_id=event_folder["id"]
            )
        )

        report_version.drive_file_id = drive_file_id

        db.commit()

        return drive_file_id