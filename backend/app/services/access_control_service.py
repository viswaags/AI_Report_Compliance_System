from app.models.club_membership import ClubMembership
from app.models.event import Event
from app.models.report import Report


class AccessControlService:

    @staticmethod
    def user_has_club_access(
        db,
        user_id: int,
        club_id: int
    ) -> bool:

        membership = (
            db.query(ClubMembership)
            .filter(
                ClubMembership.user_id == user_id,
                ClubMembership.club_id == club_id,
                ClubMembership.is_active == True
            )
            .first()
        )

        return membership is not None

    @staticmethod
    def user_can_access_event(
        db,
        user_id: int,
        event_id: int
    ) -> bool:

        event = (
            db.query(Event)
            .filter(Event.id == event_id)
            .first()
        )

        if not event:
            return False

        return AccessControlService.user_has_club_access(
            db,
            user_id,
            event.club_id
        )

    @staticmethod
    def user_can_access_report(
        db,
        user_id: int,
        report_id: int
    ) -> bool:

        report = (
            db.query(Report)
            .filter(Report.id == report_id)
            .first()
        )

        if not report:
            return False

        return AccessControlService.user_can_access_event(
            db,
            user_id,
            report.event_id
        )
    @staticmethod
    def get_accessible_club_ids(
        db,
        user_id
    ):
        memberships = (
            db.query(ClubMembership)
            .filter(
                ClubMembership.user_id == user_id,
                ClubMembership.is_active == True
            )
            .all()
        )

        return [
            m.club_id
            for m in memberships
        ]