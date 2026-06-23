from app.services.validation_result_service import (
    ValidationResultService
)


class WorkflowValidationResultAgent:

    @staticmethod
    def run(state):

        validation = state["validation"]

        validation_result = (
            ValidationResultService
            .create_validation_result(
                db=state["db"],
                report_version_id=
                    state["report_version"].id,

                compliance_score=
                    validation["compliance_score"],

                issues=
                    validation["issues_json"],

                findings=
                    validation.get(
                        "compliance_findings",
                        []
                    )
            )
        )

        state["validation_result"] = (
            validation_result
        )

        return state