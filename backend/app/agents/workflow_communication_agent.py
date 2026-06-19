from app.agents.communication_agent import (
    CommunicationAgent
)


class WorkflowCommunicationAgent:

    @staticmethod
    def run(state):

        email = (
            CommunicationAgent()
            .generate_email_draft(
                state["feedback"],
                {},
                {}
            )
        )

        state["email_draft"] = email

        return state