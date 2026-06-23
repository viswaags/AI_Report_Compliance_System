from app.models.template import Template
from app.models.report import Report


class TemplateVersionService:

    @staticmethod
    def get_latest_template(db):

        return (
            db.query(Template)
            .order_by(
                Template.id.desc()
            )
            .first()
        )

    @staticmethod
    def check_report_template_status(
        db,
        report
    ):

        latest_template = (
            TemplateVersionService
            .get_latest_template(db)
        )

        if not latest_template:

            return {
                "is_latest": True,
                "current_template": None,
                "latest_template": None
            }

        return {
            "is_latest":
                report.template_id ==
                latest_template.id,

            "current_template":
                report.template_id,

            "latest_template":
                latest_template.id,

            "latest_version":
                latest_template.version
        }

    @staticmethod
    def outdated_reports_count(
        db
    ):

        latest_template = (
            TemplateVersionService
            .get_latest_template(db)
        )

        if not latest_template:
            return 0

        return (
            db.query(Report)
            .filter(
                Report.template_id !=
                latest_template.id
            )
            .count()
        )