from app.models.report import Report
from app.models.review import Review

from app.models.event import Event
from app.models.club_membership import ClubMembership
from app.models.user import User, UserRole
from app.services.email_service import EmailService
from app.models.report_version import ReportVersion


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
            "REVISION_REQUIRED"
        }:
            raise ValueError(
                "Status must be APPROVED or REVISION_REQUIRED"
            )
        
        latest_version = (
            db.query(ReportVersion)
            .filter(
                ReportVersion.report_id == report_id
            )
            .order_by(
                ReportVersion.version_no.desc()
            )
            .first()
        )

        if not latest_version:
            raise ValueError(
                "Report version not found"
            )

        existing_review = (
            db.query(Review)
            .filter(
                Review.report_version_id ==
                latest_version.id
            )
            .first()
        )

        if existing_review:
            raise ValueError(
                "This report version has already been reviewed"
            )

        review = Review(
            report_id=report_id,
            report_version_id=latest_version.id,
            reviewer_id=reviewer_id,
            status=status,
            comments=comments
        )

        report.status = status

        db.add(review)
        db.flush()
        db.refresh(review)

        return review

        '''event = (
            db.query(Event)
            .filter(
                Event.id == report.event_id
            )
            .first()
        )

        if status == "APPROVED":
            
            RecordManagementService.create_event_record(
                db=db,
                report_id=report_id,
                approved_by=reviewer_id
            )

            NotificationService.create_notification(
                db=db,
                user_id=report.created_by,
                title="Report Approved",
                message=(
                    f"Report for '{event.event_title}' has been approved."
                ),
                notification_type="REVIEW"
            )

            ReviewService.send_acceptance_email(
                db=db,
                report=report,
                comments=comments
            )

        elif status == "REVISION_REQUIRED":

            NotificationService.create_notification(
                db=db,
                user_id=report.created_by,
                title="Report Revisions Required",
                message=(
                    f"Report for '{event.event_title}' was reviewed and revisions are required."
                ),
                notification_type="REVIEW"
            )

            ReviewService.send_revision_required_email(
                db=db,
                report=report,
                comments=comments
            )

        return review'''
    
    @staticmethod
    def send_revision_required_email(
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
            subject=f"Report Revisions Required - {event.event_title}",
            body=(
                f"Your report for '{event.event_title}' "
                f"has been reviewed and revisions are required.\n\n"
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