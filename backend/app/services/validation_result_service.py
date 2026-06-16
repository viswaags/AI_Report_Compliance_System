from app.models.validation_result import ValidationResult

class ValidationResultService:


    @staticmethod
    def _normalize_issues(
        issues
    ):

        normalized_issues = []

        for issue in issues or []:

            if isinstance(issue, dict):

                normalized_issues.append(issue)

            else:

                normalized_issues.append({
                    "type": "validation_issue",
                    "field": None,
                    "severity": "medium",
                    "message": str(issue)
                })

        return normalized_issues


    @staticmethod
    def create_validation_result(
        db,
        report_version_id,
        compliance_score,
        issues
    ):

        validation_result = ValidationResult(
            report_version_id=report_version_id,
            compliance_score=compliance_score,
            issues_json=ValidationResultService._normalize_issues(
                issues
            )
        )

        db.add(validation_result)

        db.commit()

        db.refresh(validation_result)

        return validation_result

