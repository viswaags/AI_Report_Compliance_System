from app.models.template import Template

from app.services.raw_extraction_builder import (
    RawExtractionBuilder
)

from app.services.template_guided_mapper import (
    TemplateGuidedMapper
)


class DocumentProcessingAgent:

    @staticmethod
    def process(
        db,
        report,
        file_path
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

        raw_extraction = (
            RawExtractionBuilder.build(
                file_path
            )
        )

        canonical_report_model = (
            TemplateGuidedMapper.map(
                template.schema_json,
                raw_extraction
            )
        )

        return {
            "raw_extraction":
                raw_extraction,

            "canonical_report_model":
                canonical_report_model
        }

    @staticmethod
    def run(state):

        result = (
            DocumentProcessingAgent.process(
                state["db"],
                state["report"],
                state["file_path"]
            )
        )

        state["raw_extraction"] = (
            result["raw_extraction"]
        )

        state["canonical_report_model"] = (
            result["canonical_report_model"]
        )

        return state