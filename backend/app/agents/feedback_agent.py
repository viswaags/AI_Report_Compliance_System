import json

from app.ai.openrouter_client import OpenRouterClient


class FeedbackAgent:

    def __init__(self):

        self.client = OpenRouterClient()

    def generate_feedback(
        self,
        issues_json,
        compliance_score
    ):

        prompt = f"""
You are an institutional report compliance reviewer.

Compliance Score:
{compliance_score}

Issues:
{json.dumps(issues_json, indent=2)}

Generate professional correction guidance.

Explain:
1. What is wrong.
2. What should be corrected.
3. How to improve compliance.

Keep response professional.
"""
        return """
The uploaded report does not comply with the approved template.

Issues identified:

1. Resource Person information is missing.
2. Report Title section is missing.
3. Club section is missing.
4. Required image captions were not found.
5. Minimum image count requirement is not satisfied.

Please correct these issues and resubmit the report for validation.
"""

        return self.client.generate(
            prompt
        )