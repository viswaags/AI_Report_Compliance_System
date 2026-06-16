from app.models.report_extraction import (
    ReportExtraction
)


class ReportExtractionService:

    @staticmethod
    def create_or_update(
        db,
        report_version_id,
        extracted_json
    ):

        extraction = (
            db.query(
                ReportExtraction
            )
            .filter(
                ReportExtraction.report_version_id
                ==
                report_version_id
            )
            .first()
        )

        if extraction:

            extraction.extracted_json = (
                extracted_json
            )

            db.commit()

            db.refresh(
                extraction
            )

            return extraction

        extraction = ReportExtraction(
            report_version_id=
            report_version_id,

            extracted_json=
            extracted_json
        )

        db.add(extraction)

        db.commit()

        db.refresh(extraction)

        return extraction