from sqlalchemy.orm import Session

from app.agents.communication_agent import CommunicationAgent
from app.agents.feedback_agent import FeedbackAgent
from app.models.event import Event
from app.models.feedback import Feedback
from app.models.report import Report
from app.models.report_version import ReportVersion
from app.models.validation_result import ValidationResult
from app.services.email_service import EmailService
from app.models.club_membership import ClubMembership
from app.models.user import User, UserRole


class FeedbackService:

    @staticmethod
    def generate_feedback(
        db: Session,
        validation_result_id: int
    ):
        validation_result = FeedbackService._get_validation_result(
            db,
            validation_result_id
        )

        agent = FeedbackAgent()
        feedback_text = agent.generate_feedback(
            validation_result.issues_json,
            validation_result.compliance_score
        )

        feedback = Feedback(
            validation_result_id=validation_result.id,
            feedback_text=feedback_text,
            model_used="openrouter/free"
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return feedback

    @staticmethod
    def generate_feedback_bundle(
        db: Session,
        validation_result_id: int
    ):
        validation_result = FeedbackService._get_validation_result(
            db,
            validation_result_id
        )
        feedback = FeedbackService.generate_feedback(
            db,
            validation_result_id
        )
        report, event = FeedbackService._report_and_event_for_validation(
            db,
            validation_result
        )
        email_draft = CommunicationAgent().generate_email_draft(
            feedback.feedback_text,
            FeedbackService._model_dict(report),
            FeedbackService._model_dict(event)
        )

        student_emails = (
            FeedbackService
            .get_student_representative_emails(
                db,
                report.id
            )
        )

        if student_emails:

            EmailService.send_email(
                recipients=student_emails,
                subject=email_draft["email_subject"],
                body=email_draft["email_body"]
            )

        return {
            "feedback": feedback.feedback_text,
            "feedback_id": feedback.id,
            "email_subject": email_draft["email_subject"],
            "email_body": email_draft["email_body"],
        }

    @staticmethod
    def latest_feedback_for_report(db: Session, report_id: int):
        latest_validation = FeedbackService.latest_validation_for_report(
            db,
            report_id
        )
        if not latest_validation:
            return None

        return (
            db.query(Feedback)
            .filter(Feedback.validation_result_id == latest_validation.id)
            .order_by(Feedback.id.desc())
            .first()
        )

    @staticmethod
    def latest_email_draft_for_report(db: Session, report_id: int):
        feedback = FeedbackService.latest_feedback_for_report(db, report_id)
        if not feedback:
            return None

        validation_result = FeedbackService._get_validation_result(
            db,
            feedback.validation_result_id
        )
        report, event = FeedbackService._report_and_event_for_validation(
            db,
            validation_result
        )
        return CommunicationAgent().generate_email_draft(
            feedback.feedback_text,
            FeedbackService._model_dict(report),
            FeedbackService._model_dict(event)
        )

    @staticmethod
    def latest_validation_for_report(db: Session, report_id: int):
        return (
            db.query(ValidationResult)
            .join(
                ReportVersion,
                ValidationResult.report_version_id == ReportVersion.id
            )
            .filter(ReportVersion.report_id == report_id)
            .order_by(ValidationResult.id.desc())
            .first()
        )

    @staticmethod
    def _get_validation_result(db: Session, validation_result_id: int):
        validation_result = (
            db.query(ValidationResult)
            .filter(ValidationResult.id == validation_result_id)
            .first()
        )
        if not validation_result:
            raise ValueError("Validation result not found")
        return validation_result

    @staticmethod
    def _report_and_event_for_validation(db: Session, validation_result):
        report_version = (
            db.query(ReportVersion)
            .filter(ReportVersion.id == validation_result.report_version_id)
            .first()
        )
        report = None
        event = None
        if report_version:
            report = (
                db.query(Report)
                .filter(Report.id == report_version.report_id)
                .first()
            )
        if report:
            event = (
                db.query(Event)
                .filter(Event.id == report.event_id)
                .first()
            )
        return report, event

    @staticmethod
    def _model_dict(model):
        if not model:
            return {}

        return {
            column.name: getattr(model, column.name)
            for column in model.__table__.columns
        }
    
    @staticmethod
    def get_student_representative_emails(
        db,
        report_id
    ):
        from app.models.report import Report
        from app.models.event import Event

        report = (
            db.query(Report)
            .filter(Report.id == report_id)
            .first()
        )

        if not report:
            return []

        event = (
            db.query(Event)
            .filter(Event.id == report.event_id)
            .first()
        )

        if not event:
            return []

        memberships = (
            db.query(ClubMembership)
            .filter(
                ClubMembership.club_id == event.club_id,
                ClubMembership.role == UserRole.STUDENT_REPRESENTATIVE,
                ClubMembership.is_active == True
            )
            .all()
        )

        emails = []

        for membership in memberships:

            user = (
                db.query(User)
                .filter(User.id == membership.user_id)
                .first()
            )

            if user:
                emails.append(user.email)

        return emails
    
    @staticmethod
    def send_feedback_email(
        db,
        report_id
    ):
        email_draft = (
            FeedbackService
            .latest_email_draft_for_report(
                db,
                report_id
            )
        )

        if not email_draft:
            return

        recipients = (
            FeedbackService
            .get_student_representative_emails(
                db,
                report_id
            )
        )

        if not recipients:
            return

        EmailService.send_email(
            recipients=recipients,
            subject=email_draft["email_subject"],
            body=email_draft["email_body"]
        )
