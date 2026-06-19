from app.agents.feedback_agent import (
    FeedbackAgent
)


class WorkflowFeedbackAgent:

    @staticmethod
    def run(state):

        validation = state["validation"]

        feedback = (
            FeedbackAgent()
            .generate_feedback(
                validation["issues_json"],
                validation["compliance_score"]
            )
        )

        state["feedback"] = feedback

        return state