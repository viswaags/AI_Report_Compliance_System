from app.models.report import Report
from app.models.review import Review
from app.services.record_management_service import (
    RecordManagementService
)


class ReviewService:

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

        if report.status != "COMPLIANCE_PASSED":
            raise ValueError(
                "Only COMPLIANCE_PASSED reports can be reviewed"
            )

        if status not in {
            "APPROVED",
            "REJECTED"
        }:
            raise ValueError(
                "Status must be APPROVED or REJECTED"
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

        if status == "APPROVED":

            RecordManagementService.create_event_record(
                db=db,
                report_id=report_id,
                approved_by=reviewer_id
            )

        return review