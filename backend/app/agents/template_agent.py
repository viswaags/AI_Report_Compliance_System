from app.services.template_service import (
    TemplateService
)

from app.services.template_analyzer import (
    TemplateAnalyzer
)


class TemplateAgent:

    @staticmethod
    def get_latest_template(db):

        return (
            TemplateService
            .get_latest_template(db)
        )

    @staticmethod
    def analyze_template(
        file_path,
        version
    ):

        return (
            TemplateAnalyzer
            .analyze_file(
                file_path=file_path,
                version=version
            )
        )

    @staticmethod
    def validate_template_version(
        db,
        template_id
    ):

        latest_template = (
            TemplateService
            .get_latest_template(db)
        )

        if not latest_template:
            return False

        return (
            latest_template.id
            == template_id
        )