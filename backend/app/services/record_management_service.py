from app.models.event import Event
from app.models.event_record import EventRecord
from app.models.report import Report
from app.models.report_extraction import ReportExtraction
from app.models.report_version import ReportVersion


class RecordManagementService:

    @staticmethod
    def create_event_record(
        db,
        report_id: int,
        approved_by: int
    ):

        report = (
            db.query(Report)
            .filter(
                Report.id == report_id
            )
            .first()
        )

        if not report:
            raise ValueError(
                "Report not found"
            )

        event = (
            db.query(Event)
            .filter(
                Event.id == report.event_id
            )
            .first()
        )

        latest_version = (
            db.query(ReportVersion)
            .filter(
                ReportVersion.report_id == report.id
            )
            .order_by(
                ReportVersion.version_no.desc()
            )
            .first()
        )

        extraction = (
            db.query(ReportExtraction)
            .filter(
                ReportExtraction.report_version_id ==
                latest_version.id
            )
            .first()
        )

        participant_count = None

        if extraction:

            canonical = (
                extraction.extracted_json
                .get("canonical_report_model", {})
            )

            participant_count = (
                canonical
                .get("event_information_table", {})
                .get("number_of_participants")
            )

        record = EventRecord(
            club_id=event.club_id,
            event_id=event.id,
            report_id=report.id,
            event_title=event.event_title,
            event_category=event.event_category,
            event_date=event.event_date,
            participant_count=participant_count,
            approved_by=approved_by
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record