from app.services.record_management_service import (
    RecordManagementService
)


class RecordManagementAgent:

    @staticmethod
    def archive(
        db,
        report_id,
        approved_by
    ):

        return (
            RecordManagementService
            .create_event_record(
                db,
                report_id,
                approved_by
            )
        )