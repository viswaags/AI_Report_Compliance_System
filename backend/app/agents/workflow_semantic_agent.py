from app.agents.semantic_validation_agent import (
    SemanticValidationAgent
)


class WorkflowSemanticAgent:

    @staticmethod
    def run(state):

        canonical_report_model = (
            state["canonical_report_model"]
        )

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
            SemanticValidationAgent
            .validate(
                canonical_report_model,
                event_title
            )
        )

        state["semantic_issues"] = (
            semantic_issues
        )

        state["validation"].setdefault(
            "issues_json",
            []
        )

        state["validation"][
            "issues_json"
        ].extend(
            semantic_issues
        )

        if semantic_issues:

            state["validation"]["compliance_score"] = max(
                0,
                state["validation"]["compliance_score"]
                - (len(semantic_issues) * 5)
            )

            state["validation"]["status"] = "failed"

        return state