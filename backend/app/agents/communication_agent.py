import json

from app.ai.gemini_client import GeminiClient


class CommunicationAgent:

    def __init__(self):
        self.client = GeminiClient()

    def generate_email_draft(
        self,
        feedback,
        report,
        event
    ):
        prompt = f"""
You draft professional institutional correction emails.

Do not send an email. Generate only a subject and body.

Feedback:
{feedback}

Report:
{json.dumps(report, default=str, indent=2)}

Event:
{json.dumps(event, default=str, indent=2)}

Return strict JSON with:
{{
  "email_subject": "...",
  "email_body": "..."
}}
"""
        response = self.client.generate(prompt)
        return CommunicationAgent._parse_response(response)

    @staticmethod
    def _parse_response(response):
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "email_subject": "Report corrections required",
                "email_body": response,
            }

        return {
            "email_subject": data.get("email_subject", "Report corrections required"),
            "email_body": data.get("email_body", ""),
        }
