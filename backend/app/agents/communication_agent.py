from app.services.email_service import (
    EmailService
)

from app.services.notification_service import (
    NotificationService
)


class CommunicationAgent:

    def generate_email_draft(
        self,
        feedback,
        report,
        event
    ):

        event_title = (
            event.get("event_title")
            if event else "Event"
        )

        return {
            "email_subject":
                f"Report Corrections Required - {event_title}",

            "email_body":
                (
                    "Dear Student Representative,\n\n"
                    "The submitted report requires corrections "
                    "before it can proceed for approval.\n\n"
                    f"{feedback}\n\n"
                    "Please revise the report and resubmit.\n\n"
                    "Regards,\n"
                    "AI Report Compliance System"
                )
        }

    @staticmethod
    def send_email(
        recipients,
        subject,
        body
    ):

        EmailService.send_email(
            recipients=recipients,
            subject=subject,
            body=body
        )

    @staticmethod
    def send_notification(
        db,
        user_id,
        title,
        message,
        notification_type="SYSTEM"
    ):

        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type
        )