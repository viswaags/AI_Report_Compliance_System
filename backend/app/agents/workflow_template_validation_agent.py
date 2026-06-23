class WorkflowTemplateValidationAgent:

    @staticmethod
    def run(state):

        schema = state["template_analysis"]

        if not schema:
            raise ValueError(
                "Template analysis failed"
            )
        
        if not schema.get("document_order"):
            raise ValueError(
                "Template document order missing"
            )

        if not schema.get("page_constraints"):
            raise ValueError(
                "Template page constraints missing"
            )

        required_components = [
            "header",
            "report_title",
            "event_information_table",
            "summary",
            "signatures"
        ]

        components = (
            schema.get(
                "components",
                {}
            )
        )

        missing = []

        for component in required_components:

            if component not in components:

                missing.append(component)
        
        if missing:
            raise ValueError(
                f"Missing required template components: {missing}"
            )

        state["template_validation"] = {
            "valid": True,
            "missing_components": missing
        }

        print("Template validation completed.")

        return state