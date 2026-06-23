from app.models.notification import Notification


class NotificationService:

    @staticmethod
    def create_notification(
        db,
        user_id,
        title,
        message,
        notification_type="GENERAL"
    ):

        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type
        )

        db.add(notification)

        db.commit()

        db.refresh(notification)

        return notification

    @staticmethod
    def get_user_notifications(
        db,
        user_id
    ):

        return (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id
            )
            .order_by(
                Notification.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def unread_count(
        db,
        user_id
    ):

        return (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .count()
        )

    @staticmethod
    def mark_as_read(
        db,
        notification_id,
        user_id
    ):

        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
            .first()
        )

        if not notification:
            return None

        notification.is_read = True

        db.commit()

        db.refresh(notification)

        return notification

    @staticmethod
    def mark_all_as_read(
        db,
        user_id
    ):

        notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .all()
        )

        for notification in notifications:
            notification.is_read = True

        db.commit()

        return {
            "message":
            "All notifications marked as read"
        }