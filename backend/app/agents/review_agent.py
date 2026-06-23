from app.services.review_service import (
    ReviewService
)


class ReviewAgent:

    @staticmethod
    def approve(
        db,
        report_id,
        reviewer_id,
        comments=None
    ):

        return (
            ReviewService.create_review(
                db=db,
                report_id=report_id,
                reviewer_id=reviewer_id,
                status="APPROVED",
                comments=comments
            )
        )

    @staticmethod
    def request_revision(
        db,
        report_id,
        reviewer_id,
        comments=None
    ):

        return (
            ReviewService.create_review(
                db=db,
                report_id=report_id,
                reviewer_id=reviewer_id,
                status="REVISION_REQUIRED",
                comments=comments
            )
        )