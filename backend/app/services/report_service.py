from app.models.report import Report


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

            db.commit()

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

        db.commit()

        db.refresh(report)

        return report.current_version