from app.models.review import Review
from app.models.report import Report


class ReviewService:

    VALID_REVIEW_STATUSES = {
        "UNDER_REVIEW",
        "APPROVED",
        "REJECTED"
    }

    @staticmethod
    def create_review(
        db,
        report_id,
        reviewer_id,
        status,
        comments
    ):

        report = (
            db.query(Report)
            .filter(
                Report.id == report_id
            )
            .first()
        )

        if not report:
            raise ValueError(
                "Report not found"
            )

        if status not in (
            ReviewService
            .VALID_REVIEW_STATUSES
        ):
            raise ValueError(
                "Invalid review status"
            )

        if (
            report.status
            !=
            "COMPLIANCE_PASSED"
            and
            status == "APPROVED"
        ):
            raise ValueError(
                "Report must pass compliance first"
            )

        review = Review(
            report_id=report_id,
            reviewer_id=reviewer_id,
            status=status,
            comments=comments
        )

        db.add(review)

        db.commit()

        db.refresh(review)

        return review