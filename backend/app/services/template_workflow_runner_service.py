from app.workflows.template_workflow import (
    TemplateWorkflow
)


class TemplateWorkflowRunnerService:

    @staticmethod
    def run(
        db,
        file_path,
        version,
        drive_file_id=None
    ):

        workflow = (
            TemplateWorkflow
            .build()
        )

        result = workflow.invoke(
            {
                "db": db,
                "file_path": file_path,
                "version": version,
                "drive_file_id": drive_file_id
            }
        )

        return result