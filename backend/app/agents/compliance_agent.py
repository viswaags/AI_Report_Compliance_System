from app.models.template import Template

from app.services.compliance_engine import (
    ComplianceEngine
)

from app.services.template_service import (
    TemplateService
)


class ComplianceAgent:

    @staticmethod
    def validate(
        db,
        report,
        canonical_report_model
    ):

        template = (
            db.query(Template)
            .filter(
                Template.id == report.template_id
            )
            .first()
        )

        if not template:
            raise ValueError(
                "Template not found"
            )

        latest_template = (
            TemplateService
            .get_latest_template(db)
        )

        latest_template_check = (
            latest_template is not None
            and latest_template.id == template.id
        )

        return (
            ComplianceEngine.validate(
                template.schema_json,
                canonical_report_model,
                latest_template_check
            )
        )

    @staticmethod
    def run(state):

        validation = (
            ComplianceAgent.validate(
                state["db"],
                state["report"],
                state["canonical_report_model"]
            )
        )

        state["validation"] = validation

        return state
'''
from app.models.template import Template

from app.services.compliance_engine import (
    ComplianceEngine
)

from app.services.template_service import (
    TemplateService
)


class ComplianceAgent:

    @staticmethod
    def run(state):

        db = state["db"]

        report = state["report"]

        template = (
            db.query(Template)
            .filter(
                Template.id == report.template_id
            )
            .first()
        )

        latest_template = (
            TemplateService
            .get_latest_template(db)
        )

        latest_template_check = (
            latest_template is not None
            and latest_template.id == template.id
        )

        validation = (
            ComplianceEngine.validate(
                template.schema_json,
                state["canonical_report_model"],
                latest_template_check
            )
        )

        state["validation"] = validation

        return state

        '''