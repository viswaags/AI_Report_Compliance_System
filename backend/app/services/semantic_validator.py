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

        if not summary:
            return []

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
You are a semantic consistency validator for a college event report.

Your task is ONLY to verify whether the Event Summary is factually consistent with the Event Information.

========================
EVENT TITLE
========================
{event_title}

========================
EVENT INFORMATION
========================
{json.dumps(event_table, indent=2)}

========================
EVENT SUMMARY
========================
{summary}

Carefully compare the Event Summary against the Event Information.

Report an issue ONLY when there is a clear factual inconsistency.

Check ONLY the following:
Check ONLY the following.

1. Event Consistency

The summary must describe the same event as the Event Title.

If the summary clearly refers to a different event, report it.


2. Event Information Table Semantic Consistency

Verify that every field in the Event Information contains the correct type of information.

Club
- should contain a club name.
- should NOT contain an event title.
- should NOT contain a venue.
- should NOT contain a person name.
- should NOT contain participant counts.

Event Title
- should contain the title of the event.
- should NOT contain a club name.
- should NOT contain a venue.
- should NOT contain a person name.

Event Category
- should describe the event category such as:
  Workshop
  Seminar
  Guest Lecture
  Hackathon
  Technical Talk
  Coding Contest
  Awareness Programme
  Industrial Visit

Venue
- should contain a hall, room, lab, auditorium, campus location or online platform.

Coordinator / Organizer
- should contain one or more person names.

Resource Person
- should contain one or more person names.

Number of Participants
- should contain only the participant count.

Date & Duration
- should contain a date and/or time.

If a value clearly belongs to another field, report a semantic issue.

Examples

Club:
AI with Python Workshop

Event Title:
Coding Club

Venue:
Dr. S. Vaishnavi

Coordinator:
CSE Seminar Hall

These are semantic mismatches.


3. Name Consistency

Verify that names mentioned in the summary do not contradict the Event Information.

This includes

- Club
- Resource Person
- Coordinator
- Venue
- Department
- Named entities


4. Numeric Consistency

Verify that all numbers are consistent.

Treat numeric words and digits as EXACTLY equivalent.

Examples

55 = Fifty Five

120 = One Hundred Twenty

25 = Twenty Five

Do NOT report these as inconsistencies.

Only report when the values are actually different.

Examples

55 vs 60

→ Report

55 vs Fifty Five

→ Do NOT report


5. Date Consistency

Report if the summary mentions a different event date or duration.


6. Venue Consistency

Report only when the venue clearly differs.


7. Resource Person Consistency

Report only when the resource person clearly differs.


8. Participant Consistency

Report only when participant counts actually differ.


9. Event Category Consistency

Report only when the category clearly differs.


10. Event Title vs Event Table

Verify that the Event Title matches the Event Title stored inside the Event Information table.

Example

Report Title

AI with Python Workshop

Event Table

Event Title

Coding Club

Report this inconsistency.

Do NOT evaluate

- Grammar
- English quality
- Writing style
- Formatting
- Section order
- Missing sections
- Missing images
- Missing captions
- Missing signatures
- Page layout
- Header alignment
- Compliance issues already handled by rule-based validation.

Only evaluate factual semantic consistency.

If the summary is factually consistent with the Event Information, return no issues.

Severity Guidelines:

LOW
Minor inconsistency that does not change the meaning.

MEDIUM
Single factual contradiction such as an incorrect participant count, venue, date or name.

HIGH
Summary describes an entirely different event or contains multiple factual contradictions.

Each issue must contain:

- severity
- message

The message must:
- be one concise sentence
- describe only the detected inconsistency
- not suggest corrections
- not explain how to rewrite the summary

Be conservative.

Only report an issue when you are highly confident.

If there is any reasonable ambiguity, do NOT report an issue.

Prefer false negatives over false positives.

Do not guess.

Do not infer missing information.

Do not invent inconsistencies.

Do not report obvious synonyms.

For example

Coding Club
Programming Club

may refer to the same club.

Workshop
Hands-on Workshop

may refer to the same category.

Only report clear contradictions.

Return ONLY valid JSON.

Example:

{{
  "issues": [
    {{
      "severity": "MEDIUM",
      "message": "Participant count in the summary does not match the event information."
    }},
    {{
      "severity": "HIGH",
      "message": "The summary describes a different event than the event title."
    }}
  ]
}}

If there are no issues return exactly:

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