from app.models.report import Report
from app.models.review import Review
from app.services.record_management_service import (
    RecordManagementService
)
from app.models.event import Event
from app.models.club_membership import ClubMembership
from app.models.user import User, UserRole
from app.services.email_service import EmailService


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

            ReviewService.send_acceptance_email(
                db=db,
                report=report,
                comments=comments
            )

        elif status == "REJECTED":

            ReviewService.send_rejection_email(
                db=db,
                report=report,
                comments=comments
            )

        return review
    
    @staticmethod
    def send_rejection_email(
        db,
        report,
        comments
    ):
        event = (
            db.query(Event)
            .filter(Event.id == report.event_id)
            .first()
        )

        if not event:
            return

        memberships = (
            db.query(ClubMembership)
            .filter(
                ClubMembership.club_id == event.club_id,
                ClubMembership.role == UserRole.STUDENT_REPRESENTATIVE,
                ClubMembership.is_active == True
            )
            .all()
        )

        recipients = []

        for membership in memberships:

            user = (
                db.query(User)
                .filter(User.id == membership.user_id)
                .first()
            )

            if user:
                recipients.append(user.email)

        if not recipients:
            return

        EmailService.send_email(
            recipients=recipients,
            subject=f"Report Rejected - {event.event_title}",
            body=(
                f"Your report for '{event.event_title}' "
                f"has been rejected.\n\n"
                f"Comments:\n{comments}\n\n"
                f"Please revise and resubmit.\n\n"
                f"Regards,\n"
                f"AI Report Compliance System"
            )
        )

    @staticmethod
    def send_acceptance_email(
        db,
        report,
        comments
    ):
        event = (
            db.query(Event)
            .filter(Event.id == report.event_id)
            .first()
        )

        if not event:
            return

        memberships = (
            db.query(ClubMembership)
            .filter(
                ClubMembership.club_id == event.club_id,
                ClubMembership.role == UserRole.STUDENT_REPRESENTATIVE,
                ClubMembership.is_active == True
            )
            .all()
        )

        recipients = []

        for membership in memberships:

            user = (
                db.query(User)
                .filter(User.id == membership.user_id)
                .first()
            )

            if user:
                recipients.append(user.email)

        if not recipients:
            return

        EmailService.send_email(
            recipients=recipients,
            subject=f"Report Accepted - {event.event_title}",
            body=(
                f"Your report for '{event.event_title}' "
                f"has been accepted.\n\n"
                f"Comments:\n{comments}\n\n"
                f"Please proceed with the next steps.\n\n"
                f"Regards,\n"
                f"AI Report Compliance System"
            )
        )