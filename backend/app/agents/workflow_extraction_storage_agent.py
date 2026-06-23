from app.services.report_extraction_service import (
    ReportExtractionService
)


class WorkflowExtractionStorageAgent:

    @staticmethod
    def run(state):

        extraction = (
            ReportExtractionService
            .create_or_update(
                db=state["db"],
                report_version_id=
                    state["report_version"].id,
                extracted_json={
                    "raw_extraction":
                        state["raw_extraction"],

                    "canonical_report_model":
                        state["canonical_report_model"]
                }
            )
        )

        state["extraction"] = extraction

        return state