from app.services.review_service import (
    ReviewService
)


class WorkflowReviewAgent:

    @staticmethod
    def run(state):

        review = (
            ReviewService.create_review(
                db=state["db"],
                report_id=state["report_id"],
                reviewer_id=state["reviewer_id"],
                status=state["review_status"],
                comments=state["comments"]
            )
        )

        state["review"] = review

        return state