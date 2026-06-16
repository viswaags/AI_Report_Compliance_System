from app.models.report_version import ReportVersion


class ReportVersionService:

    @staticmethod
    def get_latest_version(
        db,
        report_id
    ):

        return (
            db.query(ReportVersion)
            .filter(
                ReportVersion.report_id
                == report_id
            )
            .order_by(
                ReportVersion.version_no.desc()
            )
            .first()
        )

    @staticmethod
    def create_version(
        db,
        report_id,
        version_no,
        file_path
    ):

        version = ReportVersion(
            report_id=report_id,
            version_no=version_no,
            drive_file_id=None,
            file_path=file_path
        )

        db.add(version)

        db.commit()

        db.refresh(version)

        return version