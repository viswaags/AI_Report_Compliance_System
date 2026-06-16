from app.models.report import Report
from app.models.review import Review


class ReviewService:

    VALID_TRANSITIONS = {
        "COMPLIANCE_PASSED": {
            "PENDING_COORDINATOR_REVIEW"
        },

        "PENDING_COORDINATOR_REVIEW": {
            "APPROVED",
            "REJECTED"
        }
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
            .filter(Report.id == report_id)
            .first()
        )

        if not report:
            raise ValueError("Report not found")

        allowed_statuses = ReviewService.VALID_TRANSITIONS.get(
            report.status,
            set()
        )
        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid review transition from {report.status} to {status}"
            )

        review = Review(
            report_id=report_id,
            reviewer_id=reviewer_id,
            status=status,
            comments=comments
        )
        report.status = status

        db.add(review)
        db.commit()
        db.refresh(review)

        return review
