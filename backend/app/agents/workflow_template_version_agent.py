from app.services.template_service import (
    TemplateService
)


class WorkflowTemplateVersionAgent:

    @staticmethod
    def run(state):

        latest = (
            TemplateService
            .get_latest_template(
                state["db"]
            )
        )

        state["template_version_check"] = {
            "latest_template":
                latest,

            "is_first_template":
                latest is None
        }

        print("Template version check completed.")

        return state