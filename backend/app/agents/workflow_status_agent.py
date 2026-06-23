from app.services.report_service import (
    ReportService
)


class WorkflowStatusAgent:

    @staticmethod
    def run(state):

        report = state["report"]

        validation = state["validation"]

        if validation["status"] == "passed":

            ReportService.update_status(
                state["db"],
                report.id,
                "COMPLIANCE_PASSED"
            )

        else:

            ReportService.update_status(
                state["db"],
                report.id,
                "CORRECTION_REQUIRED"
            )

        return state