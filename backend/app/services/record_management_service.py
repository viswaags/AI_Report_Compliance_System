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

        existing_record = (
            db.query(EventRecord)
            .filter(
                EventRecord.report_id == report_id
            )
            .first()
        )

        if existing_record:
            raise ValueError(
                "Event record already exists"
            )

        event = (
            db.query(Event)
            .filter(
                Event.id == report.event_id
            )
            .first()
        )

        if not event:
            raise ValueError(
                "Event not found"
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

        if not latest_version:
            raise ValueError(
                "Report version not found"
            )

        extraction = (
            db.query(ReportExtraction)
            .filter(
                ReportExtraction.report_version_id
                == latest_version.id
            )
            .first()
        )

        participant_count = None
        venue = None
        coordinators_organizers = None

        if extraction:

            canonical = (
                extraction.extracted_json
                .get(
                    "canonical_report_model",
                    {}
                )
            )

            fields = (
                canonical
                .get(
                    "event_information_table",
                    {}
                )
                .get(
                    "fields",
                    {}
                )
            )

            participant_count = (
                fields.get(
                    "number_of_participants"
                )
            )

            venue = (
                fields.get(
                    "venue"
                )
            )

            coordinators_organizers = (
                fields.get(
                    "coordinators_organizers"
                )
            )

            if participant_count:

                try:

                    participant_count = int(
                        str(
                            participant_count
                        ).strip()
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    participant_count = None

        record = EventRecord(
            club_id=event.club_id,
            event_id=event.id,
            report_id=report.id,
            event_title=event.event_title,
            event_category=event.event_category,
            event_date=event.event_date,
            venue=venue,
            participant_count=participant_count,
            coordinators_organizers=coordinators_organizers,
            approved_by=approved_by
        )

        db.add(record)

        db.commit()

        db.refresh(record)

        return record