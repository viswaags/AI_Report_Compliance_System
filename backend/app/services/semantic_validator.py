import json

from app.ai.gemini_client import GeminiClient
from app.ai.openrouter_client import OpenRouterClient


class SemanticValidator:

    @staticmethod
    def validate(
        canonical_report_model,
        event_title,
        use_openrouter=True
    ):

        summary = (
            canonical_report_model
            .get("summary", {})
            .get("content", "")
        )

        if not summary or len(summary.strip()) < 20:

            return [
                {
                    "rule_id":
                        "SEMANTIC_VALIDATION",

                    "category":
                        "SEMANTIC_VALIDATION",

                    "severity":
                        "HIGH",

                    "status":
                        "FAILED",

                    "expected":
                        "Meaningful event summary",

                    "actual":
                        summary,

                    "message":
                        "Summary is too short for semantic validation"
                }
            ]

        event_table = (
            canonical_report_model
            .get(
                "event_information_table",
                {}
            )
            .get(
                "fields",
                {}
            )
        )

        prompt = f"""
You are validating a college event report.

Event Title:
{event_title}

Metadata:
{json.dumps(event_table, indent=2)}

Summary:
{summary}

Check the following:

1. Is the summary related to the event title?
2. Is the summary meaningful?
3. Does the summary contradict metadata?
4. Are participant details reasonable?
5. Is there suspicious, unrelated, or irrelevant content?
6. Does the summary appear copied from another event?
7. Does the summary appear fake or AI-generated nonsense?

Return ONLY valid JSON.

Example:

{{
  "issues": [
    {{
      "severity": "medium",
      "message": "Summary appears unrelated to event title."
    }}
  ]
}}

If no issues exist return:

{{
  "issues": []
}}
"""

        try:

            if use_openrouter:

                response = (
                    OpenRouterClient()
                    .generate(prompt)
                )

                if (
                    not response
                    or "failed" in response.lower()
                    or "error" in response.lower()
                    or "configuration error" in response.lower()
                ):

                    response = (
                        GeminiClient()
                        .generate(prompt)
                    )

            else:

                response = (
                    GeminiClient()
                    .generate(prompt)
                )

            start = response.find("{")
            end = response.rfind("}")

            if start == -1 or end == -1:
                return []

            parsed = json.loads(
                response[start:end + 1]
            )

            semantic_issues = []

            for issue in parsed.get(
                "issues",
                []
            ):

                semantic_issues.append(
                    {
                        "rule_id":
                            "SEMANTIC_VALIDATION",

                        "category":
                            "SEMANTIC_VALIDATION",

                        "severity":
                            issue.get(
                                "severity",
                                "MEDIUM"
                            ).upper(),

                        "status":
                            "FAILED",

                        "expected":
                            (
                                "Event summary must be "
                                "semantically consistent "
                                "with metadata"
                            ),

                        "actual":
                            issue.get(
                                "message",
                                ""
                            ),

                        "message":
                            issue.get(
                                "message",
                                "Semantic validation failed"
                            )
                    }
                )

            return semantic_issues

        except Exception as exc:

            print(
                f"Semantic validation failed: {exc}"
            )

            return []