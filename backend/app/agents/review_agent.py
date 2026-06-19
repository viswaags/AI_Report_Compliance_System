from app.services.review_service import (
    ReviewService
)


class ReviewAgent:

    @staticmethod
    def review(
        db,
        report_id,
        reviewer_id,
        status,
        comments
    ):

        return (
            ReviewService.create_review(
                db=db,
                report_id=report_id,
                reviewer_id=reviewer_id,
                status=status,
                comments=comments
            )
        )