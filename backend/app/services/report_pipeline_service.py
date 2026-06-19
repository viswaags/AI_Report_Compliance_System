from app.models.template import Template
from app.services.compliance_engine import ComplianceEngine
from app.services.raw_extraction_builder import RawExtractionBuilder
from app.services.report_extraction_service import ReportExtractionService
from app.services.report_service import ReportService
from app.services.template_guided_mapper import TemplateGuidedMapper
from app.services.template_service import TemplateService
from app.services.validation_result_service import ValidationResultService
from app.services.feedback_service import FeedbackService

class ReportPipelineService:

    @staticmethod
    def process_report_version(
        db,
        report,
        report_version,
        file_path
    ):
        template = (
            db.query(Template)
            .filter(Template.id == report.template_id)
            .first()
        )

        if not template:
            raise ValueError("Template not found")

        raw_extraction = RawExtractionBuilder.build(file_path)
        canonical_report_model = TemplateGuidedMapper.map(
            template.schema_json,
            raw_extraction
        )

        latest_template = TemplateService.get_latest_template(db)
        latest_template_check = (
            latest_template is not None
            and latest_template.id == template.id
        )
        validation = ComplianceEngine.validate(
            template.schema_json,
            canonical_report_model,
            latest_template_check
        )

        ReportExtractionService.create_or_update(
            db=db,
            report_version_id=report_version.id,
            extracted_json={
                "raw_extraction": raw_extraction,
                "canonical_report_model": canonical_report_model,
            }
        )

        validation_result = ValidationResultService.create_validation_result(
            db=db,
            report_version_id=report_version.id,
            compliance_score=validation["compliance_score"],
            issues=validation["issues_json"],
            findings=validation["compliance_findings"]
        )

        if validation["status"] == "passed":
            ReportService.update_status(
                db,
                report.id,
                "COMPLIANCE_PASSED"
            )
        else:
            ReportService.update_status(
                db,
                report.id,
                "CORRECTION_REQUIRED"
            )

            feedback_bundle = (
                FeedbackService.generate_feedback_bundle(
                    db,
                    validation_result.id
                )
            )

        return {
            "raw_extraction": raw_extraction,
            "canonical_report_model": canonical_report_model,
            "validation": validation,
            "validation_result": validation_result,
        }
