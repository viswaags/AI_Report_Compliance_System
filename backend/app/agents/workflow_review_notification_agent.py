from app.models.report import Report
from app.agents.notification_agent import (
    NotificationAgent
)


class WorkflowReviewNotificationAgent:

    @staticmethod
    def run(state):

        review = state["review"]

        report = (
            state["db"]
            .query(Report)
            .filter(
                Report.id == review.report_id
            )
            .first()
        )

        if not report:
            return state

        if review.status == "APPROVED":

            NotificationAgent.notify(
                db=state["db"],
                user_id=report.created_by,
                title="Report Approved",
                message=(
                    f"Report #{report.id} has been approved."
                ),
                notification_type="REVIEW"
            )

        else:

            NotificationAgent.notify(
                db=state["db"],
                user_id=report.created_by,
                title="Revision Required",
                message=(
                    f"Report #{report.id} requires revisions."
                ),
                notification_type="REVIEW"
            )

        return state