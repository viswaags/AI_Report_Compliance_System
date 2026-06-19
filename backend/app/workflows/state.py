from typing import TypedDict


class ReportWorkflowState(TypedDict):

    db: object

    report: object

    report_version: object

    file_path: str

    raw_extraction: dict

    canonical_report_model: dict

    validation: dict

    validation_result: object

    feedback: str

    email_draft: dict