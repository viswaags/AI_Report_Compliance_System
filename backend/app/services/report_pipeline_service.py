from app.models.template import Template

from app.services.compliance_engine import (
    ComplianceEngine
)

from app.services.raw_extraction_builder import (
    RawExtractionBuilder
)

from app.services.report_extraction_service import (
    ReportExtractionService
)

from app.services.report_service import (
    ReportService
)

from app.services.template_guided_mapper import (
    TemplateGuidedMapper
)

from app.services.template_service import (
    TemplateService
)

from app.services.validation_result_service import (
    ValidationResultService
)

from app.services.feedback_service import (
    FeedbackService
)

from app.services.semantic_validator import (
    SemanticValidator
)

from app.services.notification_service import (
    NotificationService
)


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
            .filter(
                Template.id ==
                report_version.template_id
            )
            .first()
        )

        if not template:
            raise ValueError(
                "Template not found"
            )

        #
        # Raw Extraction
        #

        raw_extraction = (
            RawExtractionBuilder.build(
                file_path
            )
        )

        #
        # Template Guided Mapping
        #

        canonical_report_model = (
            TemplateGuidedMapper.map(
                template.schema_json,
                raw_extraction
            )
        )

        #
        # Latest Template Check
        #

        latest_template = (
            TemplateService
            .get_latest_template(db)
        )

        latest_template_check = (
            latest_template is not None
            and latest_template.id == template.id
        )

        #
        # Deterministic Compliance Validation
        #

        validation = (
            ComplianceEngine.validate(
                template.schema_json,
                canonical_report_model,
                latest_template_check
            )
        )

        #
        # Event Title
        #

        event_fields = (
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

        event_title = (
            event_fields.get(
                "event_title"
            )
            or event_fields.get(
                "title"
            )
            or ""
        )

        #
        # Semantic Validation
        # OpenRouter First
        # Gemini Fallback
        #

        try:

            semantic_issues = (
                SemanticValidator.validate(
                    canonical_report_model,
                    event_title,
                    use_openrouter=True
                )
            )

        except Exception as e:

            print(
                f"OpenRouter validation failed: {e}"
            )

            semantic_issues = (
                SemanticValidator.validate(
                    canonical_report_model,
                    event_title,
                    use_openrouter=False
                )
            )

        #
        # Merge Semantic Issues
        #

        validation.setdefault(
            "issues_json",
            []
        )

        validation["issues_json"].extend(
            semantic_issues
        )

        validation["issues"] = (
            validation["issues_json"]
        )

        #
        # Recalculate Validation Metrics
        #

        validation["total_checks"] += len(
            semantic_issues
        )

        failed_semantic = len(
            semantic_issues
        )

        validation["passed_checks"] = max(
            0,
            validation["passed_checks"]
            - failed_semantic
        )

        if validation["total_checks"] > 0:

            validation["compliance_score"] = round(
                (
                    validation["passed_checks"]
                    /
                    validation["total_checks"]
                ) * 100,
                2
            )

        #
        # Final Status Decision
        #

        if semantic_issues:

            validation["status"] = "failed"

        #
        # Store Extraction
        #

        ReportExtractionService.create_or_update(
            db=db,
            report_version_id=report_version.id,
            extracted_json={
                "raw_extraction":
                    raw_extraction,

                "canonical_report_model":
                    canonical_report_model,
            }
        )

        #
        # Store Validation Result
        #

        validation_result = (
            ValidationResultService
            .create_validation_result(
                db=db,
                report_version_id=
                    report_version.id,

                compliance_score=
                    validation[
                        "compliance_score"
                    ],

                issues=
                    validation[
                        "issues"
                    ],

                findings=
                    validation.get(
                        "compliance_findings",
                        []
                    )
            )
        )

        #
        # Update Report Status
        #

        if validation["status"] == "passed":

            ReportService.update_status(
                db,
                report.id,
                "COMPLIANCE_PASSED"
            )

            NotificationService.create_notification(
                db=db,
                user_id=report.created_by,
                title="Compliance Passed",
                message=(
                    f"Report #{report.id} passed compliance validation."
                ),
                notification_type="COMPLIANCE"
            )

        else:

            ReportService.update_status(
                db,
                report.id,
                "CORRECTION_REQUIRED"
            )

            NotificationService.create_notification(
                db=db,
                user_id=report.created_by,
                title="Corrections Required",
                message=(
                    f"Report #{report.id} requires corrections."
                ),
                notification_type="COMPLIANCE"
            )

            FeedbackService.generate_feedback_bundle(
                db,
                validation_result.id
            )

            #Thhis may be added in wrong place.
            db.commit()

        #
        # Return Pipeline Result
        #

        return {

            "raw_extraction":
                raw_extraction,

            "canonical_report_model":
                canonical_report_model,

            "validation":
                validation,

            "validation_result":
                validation_result
        }