from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.models.validation_result import ValidationResult

from app.agents.feedback_agent import FeedbackAgent


class FeedbackService:

    @staticmethod
    def generate_feedback(
        db: Session,
        validation_result_id: int
    ):

        validation_result = (
            db.query(
                ValidationResult
            )
            .filter(
                ValidationResult.id
                == validation_result_id
            )
            .first()
        )

        if not validation_result:
            raise Exception(
                "Validation result not found"
            )

        agent = FeedbackAgent()

        feedback_text = (
            agent.generate_feedback(
                validation_result.issues_json,
                validation_result.compliance_score
            )
        )

        feedback = Feedback(

            validation_result_id=
            validation_result.id,

            feedback_text=
            feedback_text,

            model_used=
            "google/gemini-2.5-flash"
        )

        db.add(feedback)

        db.commit()

        db.refresh(feedback)

        return feedback