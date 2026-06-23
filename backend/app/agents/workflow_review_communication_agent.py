from app.services.review_service import (
    ReviewService
)

from app.models.report import Report


class WorkflowReviewCommunicationAgent:

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

            ReviewService.send_acceptance_email(
                db=state["db"],
                report=report,
                comments=review.comments
            )

        else:

            ReviewService.send_revision_required_email(
                db=state["db"],
                report=report,
                comments=review.comments
            )

        return state