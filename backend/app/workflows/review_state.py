from typing import TypedDict


class ReviewWorkflowState(TypedDict):

    db: object

    report_id: int

    reviewer_id: int

    review_status: str

    comments: str

    review: object

    event_record: object

    notification: object