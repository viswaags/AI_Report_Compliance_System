from app.agents.communication_agent import (
    CommunicationAgent
)

from app.models.event import Event
from app.models.user import User


class WorkflowCommunicationAgent:

    @staticmethod
    def run(state):

        db = state["db"]

        report = state["report"]

        event = (
            db.query(Event)
            .filter(
                Event.id == report.event_id
            )
            .first()
        )

        user = (
            db.query(User)
            .filter(
                User.id == report.created_by
            )
            .first()
        )

        report_dict = {
            "id": report.id
        }

        event_dict = {}

        if event:

            event_dict = {
                "event_title":
                    event.event_title,

                "event_category":
                    event.event_category,

                "event_date":
                    event.event_date
            }

        email = (
            CommunicationAgent()
            .generate_email_draft(
                state["feedback"],
                report_dict,
                event_dict
            )
        )

        #
        # Store Draft
        #

        state["email_draft"] = email

        #
        # Send Email
        #

        if user and user.email:

            try:

                CommunicationAgent.send_email(
                    recipients=[
                        user.email
                    ],
                    subject=email[
                        "email_subject"
                    ],
                    body=email[
                        "email_body"
                    ]
                )

            except Exception as exc:

                print(
                    f"Email sending failed: {exc}"
                )

        return state