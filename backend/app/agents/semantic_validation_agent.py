from app.services.semantic_validator import (
    SemanticValidator
)
from app.models import canonical_report_model


class SemanticValidationAgent:

    @staticmethod
    def validate(
        canonical_report_model,
        event_title
    ):

        return (
            SemanticValidator.validate(
                canonical_report_model,
                event_title,
                use_openrouter=True
            )
        )

    @staticmethod
    def run(state):

        event_fields = (
            canonical_report_model
            .get(
                "event_information_table",
                {}
            )
            .get(
                "fields",
                {}
            )
        )

        event_title = (
            event_fields.get("event_title")
            or event_fields.get("title")
            or ""
        )

        semantic_issues = (
            SemanticValidator.validate(
                state["canonical_report_model"],
                event_title,
                use_openrouter=True
            )
        )

        state["semantic_issues"] = (
            semantic_issues
        )

        return state
    
    