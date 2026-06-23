from app.models.review import Review
from app.services.record_management_service import (
    RecordManagementService
)


class WorkflowEventRecordAgent:

    @staticmethod
    def run(state):

        review = state["review"]

        if review.status == "APPROVED":

            event_record = (
                RecordManagementService
                .create_event_record(
                    db=state["db"],
                    report_id=review.report_id,
                    approved_by=review.reviewer_id
                )
            )

            state["event_record"] = event_record

        return state