import json

from app.ai.gemini_client import GeminiClient


class FeedbackAgent:

    def __init__(self):
        self.client = GeminiClient()

    def generate_feedback(
        self,
        issues_json,
        compliance_score
    ):
        prompt = f"""
You are an institutional report compliance reviewer.

Use only the supplied compliance issues. Do not add requirements that are not present.

Compliance Score:
{compliance_score}

Issues JSON:
{json.dumps(issues_json, indent=2)}

Generate professional correction guidance that explains:
1. What is wrong.
2. Why each issue failed.
3. How the report author should correct it.

Keep the response concise, formal, and actionable.
"""
        return self.client.generate(prompt)
