from app.workflows.review_workflow import (
    ReviewWorkflow
)


class ReviewWorkflowRunnerService:

    @staticmethod
    def run(
        db,
        report_id,
        reviewer_id,
        review_status,
        comments=None
    ):

        workflow = (
            ReviewWorkflow.build()
        )

        try:

            result =  workflow.invoke(
                {
                    "db": db,
                    "report_id": report_id,
                    "reviewer_id": reviewer_id,
                    "review_status": review_status,
                    "comments": comments,
                    "review": None,
                    "event_record": None,
                    "notification": None
                }
            )

            db.commit()

        except:
            db.rollback()


        return result