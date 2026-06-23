from app.workflows.report_workflow import (
    ReportWorkflow
)


class WorkflowRunnerService:

    @staticmethod
    def run_report_workflow(
        db,
        report,
        report_version,
        file_path
    ):

        workflow = (
            ReportWorkflow.build()
        )

        initial_state = {

            "db":
                db,

            "report":
                report,

            "report_version":
                report_version,

            "file_path":
                file_path,

            "template":
                None,

            "event":
                None,

            "raw_extraction":
                {},

            "canonical_report_model":
                {},

            "validation":
                {},

            "semantic_issues":
                [],

            "validation_result":
                None,

            "feedback":
                "",

            "email_draft":
                {},

            "notification":
                None,

            "review":
                None,

            "event_record":
                None,

            "workflow_status":
                "RUNNING"
        }

        result = workflow.invoke(
            initial_state
        )

        return result