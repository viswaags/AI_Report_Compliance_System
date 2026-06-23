from app.services.notification_service import (
    NotificationService
)


class NotificationAgent:

    @staticmethod
    def notify(
        db,
        user_id,
        title,
        message,
        notification_type="SYSTEM"
    ):

        return (
            NotificationService
            .create_notification(
                db=db,
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type
            )
        )