from app.agents.feedback_agent import (
    FeedbackAgent
)

from app.models.feedback import Feedback


class WorkflowFeedbackAgent:

    @staticmethod
    def run(state):

        validation = state["validation"]

        feedback_text = (
            FeedbackAgent()
            .generate_feedback(
                validation["issues_json"],
                validation["compliance_score"]
            )
        )

        feedback_record = Feedback(
            validation_result_id=
                state["validation_result"].id,

            feedback_text=
                feedback_text,

            model_used=
                "openrouter/free"
        )

        db = state["db"]

        db.add(feedback_record)

        db.flush()

        db.refresh(feedback_record)

        state["feedback"] = feedback_text

        return state