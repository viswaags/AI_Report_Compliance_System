from typing import Any

from app.services.layout_validator import LayoutValidator
from app.services.section_order_validator import SectionOrderValidator


class ComplianceEngine:

    @staticmethod
    def validate(
        report_data,
        template_schema,
        latest_template_check=True
    ):
        issues = []
        metadata_issues = []
        header_issues = []
        image_issues = []
        signature_issues = []
        template_issues = []
        layout_issues = []
        section_issues = []

        total_checks = 0
        passed_checks = 0

        field_configs = ComplianceEngine._collect_field_configs(template_schema)
        report_fields = ComplianceEngine._report_fields(report_data)

        for field, config in field_configs.items():
            if not ComplianceEngine._is_required(config):
                continue

            total_checks += 1

            if ComplianceEngine._has_value(report_fields.get(field)):
                passed_checks += 1
            else:
                issue = ComplianceEngine._issue(
                    issue_type="missing_field",
                    field=field,
                    severity=config.get("severity", "medium"),
                    message=config.get(
                        "message",
                        f"{ComplianceEngine._label(field)} field is missing"
                    )
                )
                issues.append(issue)
                ComplianceEngine._append_category_issue(
                    field,
                    issue,
                    template_schema,
                    metadata_issues,
                    header_issues,
                    signature_issues
                )

        section_result = SectionOrderValidator.validate(
            report_data,
            template_schema
        )
        total_checks += section_result["total_checks"]
        passed_checks += section_result["passed_checks"]
        issues.extend(section_result["issues"])
        section_issues.extend(section_result["issues"])

        required_section_result = ComplianceEngine._validate_required_sections(
            report_data,
            template_schema
        )
        total_checks += required_section_result["total_checks"]
        passed_checks += required_section_result["passed_checks"]
        issues.extend(required_section_result["issues"])
        section_issues.extend(required_section_result["issues"])

        image_result = ComplianceEngine._validate_images(
            report_data,
            template_schema
        )
        total_checks += image_result["total_checks"]
        passed_checks += image_result["passed_checks"]
        issues.extend(image_result["issues"])
        image_issues.extend(image_result["issues"])

        layout_result = LayoutValidator.validate(
            report_data,
            template_schema
        )
        total_checks += layout_result["total_checks"]
        passed_checks += layout_result["passed_checks"]
        issues.extend(layout_result["issues"])
        layout_issues.extend(layout_result["issues"])

        template_result = ComplianceEngine._validate_template_rules(
            report_data,
            template_schema,
            latest_template_check
        )
        total_checks += template_result["total_checks"]
        passed_checks += template_result["passed_checks"]
        issues.extend(template_result["issues"])
        template_issues.extend(template_result["template_issues"])
        layout_issues.extend(template_result["layout_issues"])

        compliance_score = (
            0
            if total_checks == 0
            else round((passed_checks / total_checks) * 100, 2)
        )

        return {
            "status": "passed" if len(issues) == 0 else "failed",
            "compliance_score": compliance_score,
            "issues": issues,
            "metadata_issues": metadata_issues,
            "header_issues": header_issues,
            "image_issues": image_issues,
            "signature_issues": signature_issues,
            "template_issues": template_issues,
            "layout_issues": layout_issues,
            "section_issues": section_issues,
            "total_checks": total_checks,
            "passed_checks": passed_checks
        }

    @staticmethod
    def _collect_field_configs(template_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
        fields = {}

        for field in template_schema.get("required_fields", []):
            fields[field] = {"required": True}

        container_keys = {
            "sections",
            "section_order",
            "fields",
            "layout_rules",
            "validation_rules",
            "images",
            "signature_sections",
            "page_constraints",
            "version",
        }

        for section_name, section_config in template_schema.items():
            if section_name in container_keys:
                continue

            if not isinstance(section_config, dict):
                continue

            if "required_fields" in section_config:
                for field in section_config.get("required_fields", []):
                    fields.setdefault(field, {"required": True})

            for field, config in section_config.items():
                if field in {"required_fields", "zones", "layout_rules"}:
                    continue

                if isinstance(config, dict) and ComplianceEngine._looks_like_field_config(config):
                    fields.setdefault(field, config)

        fields_node = template_schema.get("fields")
        if isinstance(fields_node, dict):
            for field, config in fields_node.items():
                fields[field] = config if isinstance(config, dict) else {"required": True}
        elif isinstance(fields_node, list):
            for item in fields_node:
                if isinstance(item, str):
                    fields[item] = {"required": True}
                elif isinstance(item, dict):
                    field = item.get("key") or item.get("name") or item.get("field")
                    if field:
                        fields[field] = item

        return fields

    @staticmethod
    def _looks_like_field_config(config):
        field_keys = {
            "required",
            "label",
            "labels",
            "aliases",
            "display_name",
            "layout",
            "zone",
            "position",
            "severity"
        }
        return any(key in config for key in field_keys)

    @staticmethod
    def _report_fields(report_data):
        fields = dict(report_data.get("fields", {}))

        for section_name in ["header", "metadata_table"]:
            section = report_data.get(section_name, {})
            if isinstance(section, dict):
                fields.update(section)

        return fields

    @staticmethod
    def _validate_required_sections(report_data, template_schema):
        issues = []
        total_checks = 0
        passed_checks = 0
        sections = report_data.get("sections", {})

        for section, config in ComplianceEngine._required_sections(template_schema).items():
            total_checks += 1
            if sections.get(section, {}).get("present"):
                passed_checks += 1
            else:
                issues.append(ComplianceEngine._issue(
                    issue_type="missing_section",
                    field=section,
                    severity=config.get("severity", "medium"),
                    message=config.get(
                        "message",
                        f"{ComplianceEngine._label(section)} section is missing"
                    )
                ))

        return {
            "issues": issues,
            "total_checks": total_checks,
            "passed_checks": passed_checks
        }

    @staticmethod
    def _required_sections(template_schema):
        sections = {}

        for section in template_schema.get("required_sections", []):
            sections[section] = {"required": True}

        sections_node = template_schema.get("sections")

        if isinstance(sections_node, dict):
            for section, config in sections_node.items():
                if isinstance(config, dict) and config.get("required", False):
                    sections[section] = config
        elif isinstance(sections_node, list):
            for item in sections_node:
                if isinstance(item, str):
                    sections[item] = {"required": True}
                elif isinstance(item, dict) and item.get("required", False):
                    section = item.get("key") or item.get("name") or item.get("section")
                    if section:
                        sections[section] = item

        return sections

    @staticmethod
    def _validate_images(report_data, template_schema):
        image_rules = template_schema.get("images", {})

        if not isinstance(image_rules, dict):
            return {
                "issues": [],
                "total_checks": 0,
                "passed_checks": 0
            }

        report_images = report_data.get("images", {})
        total_checks = 0
        passed_checks = 0
        issues = []

        if image_rules.get("required", False) or "min_images" in image_rules or "max_images" in image_rules:
            total_checks += 1
            image_count = report_images.get("count", 0)
            min_images = image_rules.get("min_images", 0)
            max_images = image_rules.get("max_images")

            valid_min = image_count >= min_images
            valid_max = True if max_images is None else image_count <= max_images

            if valid_min and valid_max:
                passed_checks += 1
            else:
                issues.append(ComplianceEngine._issue(
                    issue_type="image_count",
                    field="image_count",
                    severity=image_rules.get("severity", "medium"),
                    message="Image count does not satisfy template schema",
                    expected={
                        "min_images": min_images,
                        "max_images": max_images
                    },
                    actual=image_count
                ))

        if image_rules.get("caption_required", False):
            total_checks += 1
            if report_images.get("caption_present", False):
                passed_checks += 1
            else:
                issues.append(ComplianceEngine._issue(
                    issue_type="missing_field",
                    field="image_captions",
                    severity=image_rules.get("caption_severity", "medium"),
                    message="Image captions are missing"
                ))

        return {
            "issues": issues,
            "total_checks": total_checks,
            "passed_checks": passed_checks
        }

    @staticmethod
    def _validate_template_rules(
        report_data,
        template_schema,
        latest_template_check
    ):
        layout_rules = template_schema.get("layout_rules", {})
        report_layout = report_data.get("layout", {})

        issues = []
        template_issues = []
        layout_issues = []
        total_checks = 0
        passed_checks = 0

        page_limit = layout_rules.get("page_limit") or template_schema.get("page_limit")
        if page_limit:
            total_checks += 1
            if report_layout.get("page_count") == page_limit:
                passed_checks += 1
            else:
                issue = ComplianceEngine._issue(
                    issue_type="page_count",
                    field="page_count",
                    severity=layout_rules.get("severity", "medium"),
                    message=f"Report must be exactly {page_limit} page(s)",
                    expected=page_limit,
                    actual=report_layout.get("page_count")
                )
                issues.append(issue)
                layout_issues.append(issue)

        if layout_rules.get("latest_template_required", False):
            total_checks += 1
            if latest_template_check:
                passed_checks += 1
            else:
                issue = ComplianceEngine._issue(
                    issue_type="template_version",
                    field="template",
                    severity="high",
                    message="Report is not using the latest template"
                )
                issues.append(issue)
                template_issues.append(issue)

        return {
            "issues": issues,
            "template_issues": template_issues,
            "layout_issues": layout_issues,
            "total_checks": total_checks,
            "passed_checks": passed_checks
        }

    @staticmethod
    def _append_category_issue(
        field,
        issue,
        template_schema,
        metadata_issues,
        header_issues,
        signature_issues
    ):
        if field in template_schema.get("header", {}):
            header_issues.append(issue)
        elif field in template_schema.get("metadata_table", {}).get("required_fields", []):
            metadata_issues.append(issue)
        elif field in template_schema.get("signature_sections", {}):
            signature_issues.append(issue)
        else:
            metadata_issues.append(issue)

    @staticmethod
    def _is_required(config):
        if config is True:
            return True

        if isinstance(config, dict):
            return config.get("required", True)

        return False

    @staticmethod
    def _has_value(value):
        if value is None:
            return False

        if isinstance(value, str):
            return len(value.strip()) > 0

        if isinstance(value, (list, dict)):
            return len(value) > 0

        return True

    @staticmethod
    def _issue(
        issue_type,
        field,
        severity,
        message,
        **extra
    ):
        issue = {
            "type": issue_type,
            "field": field,
            "severity": severity,
            "message": message
        }
        issue.update(extra)
        return issue

    @staticmethod
    def _label(field):
        return field.replace("_", " ").title()
