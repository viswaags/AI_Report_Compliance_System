import json

from app.ai.gemini_client import GeminiClient
from app.ai.openrouter_client import OpenRouterClient


class FeedbackAgent:

    def __init__(
        self,
        use_openrouter=True
    ):

        self.use_openrouter = use_openrouter

        if use_openrouter:
            self.client = OpenRouterClient()
        else:
            self.client = GeminiClient()

    def generate_feedback(
        self,
        issues_json,
        compliance_score
    ):
        prompt = f"""
You are a report compliance assistant.

Compliance Score:
{compliance_score}

Issues:
{json.dumps(issues_json, indent=2)}

Generate SHORT correction instructions.

Rules:
- Do not explain in detail.
- Do not provide long paragraphs.
- Mention only the issues found.
- Give simple resubmission guidance.
- Maximum 10 bullet points.

Example:

Compliance Score: 75%

Corrections Required:

1. Add Event Category field.
2. Add Number of Participants.
3. Add image captions.

Return only the feedback.
"""
        try:

            response = (
                self.client.generate(
                    prompt
                )
            )

            if (
                "AI generation failed"
                in response
                or
                "Configuration Error"
                in response
            ):
                raise Exception()

            return response

        except Exception:

            return (
                "Please review the compliance "
                "issues and resubmit the report."
            )