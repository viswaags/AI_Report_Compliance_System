from app.agents.notification_agent import (
    NotificationAgent
)
from app.models.event import Event
from app.models.club_membership import ClubMembership
from app.models.user import UserRole

class WorkflowNotificationAgent:

    @staticmethod
    def run(state):

        report = state["report"]

        validation = state["validation"]

        if validation["status"] == "passed":

            NotificationAgent.notify(
                db=state["db"],
                user_id=report.created_by,
                title="Compliance Passed",
                message=(
                    f"Report #{report.id} "
                    f"passed compliance validation."
                ),
                notification_type="COMPLIANCE"
            )

            event = (
                state["db"]
                .query(Event)
                .filter(
                    Event.id == report.event_id
                )
                .first()
            )

            if event:

                coordinators = (
                    state["db"]
                    .query(ClubMembership)
                    .filter(
                        ClubMembership.club_id == event.club_id,
                        ClubMembership.role ==
                            UserRole.CLUB_COORDINATOR,
                        ClubMembership.is_active == True
                    )
                    .all()
                )

                for coordinator in coordinators:

                    NotificationAgent.notify(
                        db=state["db"],
                        user_id=coordinator.user_id,
                        title="Review Required",
                        message=(
                            f"Report #{report.id} "
                            f"is ready for review."
                        ),
                        notification_type="REVIEW"
                    )

        else:

            NotificationAgent.notify(
                db=state["db"],
                user_id=report.created_by,
                title="Corrections Required",
                message=(
                    f"Report #{report.id} "
                    f"requires corrections."
                ),
                notification_type="COMPLIANCE"
            )

        return state