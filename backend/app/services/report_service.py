from app.models.report import Report
from app.models.report_version import ReportVersion
from sqlalchemy.orm import Session


class ReportService:

    @staticmethod
    def update_status(
        db,
        report_id,
        status
    ):

        report = (
            db.query(Report)
            .filter(
                Report.id == report_id
            )
            .first()
        )

        if report:

            report.status = status

            db.flush()

            db.refresh(report)

        return report

    @staticmethod
    def get_report(
        db,
        report_id
    ):

        return (
            db.query(Report)
            .filter(
                Report.id == report_id
            )
            .first()
        )
    
    @staticmethod
    def increment_version(
        db,
        report_id
    ):

        report = (
            db.query(Report)
            .filter(
                Report.id == report_id
            )
            .first()
        )

        if not report:
            return None

        report.current_version += 1

        db.flush()

        db.refresh(report)

        return report.current_version
    
    @staticmethod
    def get_current_report_version(
        db: Session,
        report_id: int,
        current_version: int
    ):
        return (
            db.query(ReportVersion)
            .filter(
                ReportVersion.report_id == report_id,
                ReportVersion.version_no == current_version
            )
            .first()
        )