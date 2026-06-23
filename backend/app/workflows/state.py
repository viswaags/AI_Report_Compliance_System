from typing import TypedDict


class ReportWorkflowState(TypedDict):

    db: object

    report: object

    report_version: object

    file_path: str

    template: object

    event: object

    raw_extraction: dict

    canonical_report_model: dict

    extraction: object

    validation: dict

    semantic_issues: list

    validation_result: object

    feedback: str

    feedback_record: object

    email_draft: dict

    notification: object

    review: object

    event_record: object

    workflow_status: str