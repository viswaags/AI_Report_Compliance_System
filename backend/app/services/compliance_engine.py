from typing import Any


class ComplianceEngine:

    @staticmethod
    def validate(
        template_schema,
        canonical_report_model=None,
        latest_template_check=True
    ):
        if ComplianceEngine._looks_like_report_model(template_schema):
            template_schema, canonical_report_model = (
                canonical_report_model,
                template_schema
            )

        template_schema = template_schema or {}
        canonical_report_model = canonical_report_model or {}
        components = template_schema.get("components", {})

        findings = []

        findings.extend(
            ComplianceEngine._validate_page_count(
                template_schema,
                canonical_report_model
            )
        )
        findings.extend(
            ComplianceEngine._validate_header(
                components.get("header", {}),
                canonical_report_model.get("header", {})
            )
        )
        findings.extend(
            ComplianceEngine._validate_report_title(
                components.get("report_title", {}),
                canonical_report_model.get("report_title", {})
            )
        )
        findings.extend(
            ComplianceEngine._validate_event_table(
                components.get("event_information_table", {}),
                canonical_report_model.get("event_information_table", {})
            )
        )
        findings.extend(
            ComplianceEngine._validate_summary(
                components.get("summary", {}),
                canonical_report_model.get("summary", {})
            )
        )
        findings.extend(
            ComplianceEngine._validate_images(
                components.get("images", {}),
                canonical_report_model.get("images", {})
            )
        )
        findings.extend(
            ComplianceEngine._validate_signatures(
                components.get("signatures", {}),
                canonical_report_model.get("signatures", {})
            )
        )
        findings.extend(
            ComplianceEngine._validate_document_order(
                template_schema,
                canonical_report_model
            )
        )

        findings.append(
            ComplianceEngine._finding(
                rule_id="TEMPLATE_VERSION_LATEST",
                category="DOCUMENT_STRUCTURE",
                severity="HIGH",
                status="PASSED" if latest_template_check else "FAILED",
                expected="Report uses latest template",
                actual="Latest template" if latest_template_check else "Older template",
                message=(
                    "Report uses the latest template"
                    if latest_template_check
                    else "Report is not using the latest approved template"
                )
            )
        )

        failed_findings = [
            finding
            for finding in findings
            if finding.get("status") == "FAILED"
        ]
        passed_count = len(findings) - len(failed_findings)
        compliance_score = (
            100
            if not findings
            else round((passed_count / len(findings)) * 100, 2)
        )

        return {
            "status": "passed" if not failed_findings else "failed",
            "compliance_score": compliance_score,
            "compliance_findings": findings,
            "issues_json": failed_findings,
            "issues": failed_findings,
            "total_checks": len(findings),
            "passed_checks": passed_count,
            "metadata_issues": [],
            "header_issues": ComplianceEngine._category_issues(
                failed_findings,
                "LAYOUT_VALIDATION"
            ),
            "image_issues": ComplianceEngine._category_issues(
                failed_findings,
                "IMAGE_VALIDATION"
            ),
            "signature_issues": ComplianceEngine._category_issues(
                failed_findings,
                "SIGNATURE_VALIDATION"
            ),
            "template_issues": [],
            "layout_issues": ComplianceEngine._category_issues(
                failed_findings,
                "LAYOUT_VALIDATION"
            ),
            "section_issues": ComplianceEngine._category_issues(
                failed_findings,
                "DOCUMENT_STRUCTURE"
            ),
        }

    @staticmethod
    def _validate_page_count(template_schema, report_model):
        exact_pages = template_schema.get("page_constraints", {}).get("exact_pages")
        if exact_pages is None:
            return []

        actual = report_model.get("page_count")
        return [
            ComplianceEngine._finding(
                rule_id="PAGE_EXACT_COUNT",
                category="PAGE_VALIDATION",
                severity="HIGH",
                status="PASSED" if actual == exact_pages else "FAILED",
                expected=exact_pages,
                actual=actual,
                message=(
                    f"Report has exactly {exact_pages} page(s)"
                    if actual == exact_pages
                    else f"Report must be exactly {exact_pages} page(s)"
                )
            )
        ]

    @staticmethod
    def _validate_header(header_schema, header_model):
        if not header_schema:
            return []

        findings = []
        required = header_schema.get("required", False)
        present = header_model.get("present", False)
        findings.append(
            ComplianceEngine._finding(
                rule_id="HEADER_EXISTS",
                category="DOCUMENT_STRUCTURE",
                severity="HIGH",
                status="PASSED" if present or not required else "FAILED",
                expected="Header component present" if required else "Header optional",
                actual="Present" if present else "Missing",
                message=(
                    "Header component is present"
                    if present or not required
                    else "Required header component is missing"
                )
            )
        )

        for element, config in header_schema.get("elements", {}).items():
            model_element = header_model.get("elements", {}).get(element, {})
            if config.get("required", False):
                findings.append(
                    ComplianceEngine._finding(
                        rule_id=f"HEADER_ELEMENT_{element.upper()}_EXISTS",
                        category="DOCUMENT_STRUCTURE",
                        severity="HIGH",
                        status=(
                            "PASSED"
                            if model_element.get("present")
                            else "FAILED"
                        ),
                        expected=f"{element} present",
                        actual=(
                            "Present"
                            if model_element.get("present")
                            else "Missing"
                        ),
                        message=(
                            f"{element} is present"
                            if model_element.get("present")
                            else f"Required header element '{element}' is missing"
                        )
                    )
                )

            expected_position = config.get("position")
            if expected_position and model_element.get("present"):
                actual_position = model_element.get("zone")
                findings.append(
                    ComplianceEngine._finding(
                        rule_id=f"HEADER_ELEMENT_{element.upper()}_LAYOUT",
                        category="LAYOUT_VALIDATION",
                        severity="MEDIUM",
                        status=(
                            "PASSED"
                            if actual_position == expected_position
                            else "FAILED"
                        ),
                        expected=expected_position,
                        actual=actual_position,
                        message=(
                            f"{element} is in the expected layout zone"
                            if actual_position == expected_position
                            else f"{element} is not in the expected layout zone"
                        )
                    )
                )

        return findings

    @staticmethod
    def _validate_report_title(title_schema, title_model):
        if not title_schema:
            return []

        required = title_schema.get("required", False)
        present = title_model.get("present", False)
        return [
            ComplianceEngine._finding(
                rule_id="REPORT_TITLE_EXISTS",
                category="DOCUMENT_STRUCTURE",
                severity="HIGH",
                status="PASSED" if present or not required else "FAILED",
                expected="Report title present" if required else "Report title optional",
                actual=title_model.get("text"),
                message=(
                    "Report title is present"
                    if present or not required
                    else "Required report title is missing"
                )
            )
        ]

    @staticmethod
    def _validate_event_table(table_schema, table_model):
        if not table_schema:
            return []

        findings = []
        table_required = table_schema.get("table_required", False)
        table_present = table_model.get("table_present", False)
        findings.append(
            ComplianceEngine._finding(
                rule_id="EVENT_INFORMATION_TABLE_EXISTS",
                category="TABLE_STRUCTURE",
                severity="HIGH",
                status=(
                    "PASSED"
                    if table_present or not table_required
                    else "FAILED"
                ),
                expected="Event information component must be a table",
                actual="Table present" if table_present else "Table missing",
                message=(
                    "Event information table is present"
                    if table_present or not table_required
                    else "Event information must be provided inside a table"
                )
            )
        )

        expected_order = table_schema.get("field_order", [])
        actual_order = table_model.get("field_order", [])
        comparable_actual_order = [
            field
            for field in actual_order
            if field in expected_order
        ]
        expected_present_order = [
            field
            for field in expected_order
            if field in comparable_actual_order
        ]
        findings.append(
            ComplianceEngine._finding(
                rule_id="EVENT_INFORMATION_TABLE_FIELD_ORDER",
                category="TABLE_STRUCTURE",
                severity="MEDIUM",
                status=(
                    "PASSED"
                    if comparable_actual_order == expected_present_order
                    else "FAILED"
                ),
                expected=expected_order,
                actual=comparable_actual_order,
                message=(
                    "Event information table fields are in the expected order"
                    if comparable_actual_order == expected_present_order
                    else "Event information table fields are not in the expected order"
                )
            )
        )

        fields = table_model.get("fields", {})
        for field, config in table_schema.get("fields", {}).items():
            if not config.get("required", True):
                continue

            value = fields.get(field)
            has_value = ComplianceEngine._has_value(value)
            present = field in fields and has_value
            findings.append(
                ComplianceEngine._finding(
                    rule_id=f"EVENT_TABLE_FIELD_{field.upper()}_PRESENT",
                    category="FIELD_VALIDATION",
                    severity="HIGH",
                    status="PASSED" if present else "FAILED",
                    expected=f"{config.get('label', field)} field present",
                    actual="Present" if present else "Missing",
                    message=(
                        f"{config.get('label', field)} field is present"
                        if present
                        else f"Required table field '{config.get('label', field)}' is missing"
                    )
                )
            )
            findings.append(
                ComplianceEngine._finding(
                    rule_id=f"EVENT_TABLE_FIELD_{field.upper()}_VALUE",
                    category="FIELD_VALIDATION",
                    severity="HIGH",
                    status="PASSED" if has_value else "FAILED",
                    expected=f"{config.get('label', field)} has a value",
                    actual=value,
                    message=(
                        f"{config.get('label', field)} has a value"
                        if has_value
                        else f"Required table field '{config.get('label', field)}' is empty"
                    )
                )
            )

        return findings

    @staticmethod
    def _validate_summary(summary_schema, summary_model):
        if not summary_schema:
            return []

        findings = []
        required = summary_schema.get("required", False)
        present = summary_model.get("present", False)
        findings.append(
            ComplianceEngine._finding(
                rule_id="SUMMARY_EXISTS",
                category="DOCUMENT_STRUCTURE",
                severity="HIGH",
                status="PASSED" if present or not required else "FAILED",
                expected="Summary present" if required else "Summary optional",
                actual="Present" if present else "Missing",
                message=(
                    "Summary is present"
                    if present or not required
                    else "Required summary is missing"
                )
            )
        )

        allowed_formats = summary_schema.get("allowed_formats", [])
        actual_format = summary_model.get("format")
        if allowed_formats and actual_format:
            findings.append(
                ComplianceEngine._finding(
                    rule_id="SUMMARY_FORMAT_ALLOWED",
                    category="DOCUMENT_STRUCTURE",
                    severity="MEDIUM",
                    status=(
                        "PASSED"
                        if actual_format in allowed_formats
                        else "FAILED"
                    ),
                    expected=allowed_formats,
                    actual=actual_format,
                    message=(
                        "Summary format is allowed by template"
                        if actual_format in allowed_formats
                        else "Summary format is not allowed by template"
                    )
                )
            )

        return findings

    @staticmethod
    def _validate_images(images_schema, images_model):
        if not images_schema:
            return []

        findings = []
        count = images_model.get("count", 0)
        min_images = images_schema.get("min_images", 0)
        max_images = images_schema.get("max_images")
        valid_min = count >= min_images
        valid_max = max_images is None or count <= max_images

        findings.append(
            ComplianceEngine._finding(
                rule_id="IMAGE_COUNT",
                category="IMAGE_VALIDATION",
                severity="HIGH",
                status="PASSED" if valid_min and valid_max else "FAILED",
                expected={
                    "min_images": min_images,
                    "max_images": max_images,
                },
                actual=count,
                message=(
                    "Image count satisfies template requirements"
                    if valid_min and valid_max
                    else "Image count does not satisfy template requirements"
                )
            )
        )

        if images_schema.get("caption_required", False):
            findings.append(
                ComplianceEngine._finding(
                    rule_id="IMAGE_CAPTIONS",
                    category="IMAGE_VALIDATION",
                    severity="MEDIUM",
                    status=(
                        "PASSED"
                        if images_model.get("caption_present")
                        else "FAILED"
                    ),
                    expected="At least one image caption present",
                    actual=images_model.get("captions", []),
                    message=(
                        "Image captions are present"
                        if images_model.get("caption_present")
                        else "Image captions are required by the template"
                    )
                )
            )

        return findings

    @staticmethod
    def _validate_signatures(signatures_schema, signatures_model):
        if not signatures_schema:
            return []

        findings = []
        for element, config in signatures_schema.get("elements", {}).items():
            model_element = signatures_model.get(element, {})
            if config.get("required", True):
                findings.append(
                    ComplianceEngine._finding(
                        rule_id=f"SIGNATURE_{element.upper()}_EXISTS",
                        category="SIGNATURE_VALIDATION",
                        severity="HIGH",
                        status=(
                            "PASSED"
                            if model_element.get("present")
                            else "FAILED"
                        ),
                        expected=f"{config.get('label', element)} signature present",
                        actual=(
                            "Present"
                            if model_element.get("present")
                            else "Missing"
                        ),
                        message=(
                            f"{config.get('label', element)} signature is present"
                            if model_element.get("present")
                            else f"Required signature '{config.get('label', element)}' is missing"
                        )
                    )
                )

            expected_position = config.get("position")
            actual_position = model_element.get("zone")
            if expected_position and model_element.get("present"):
                findings.append(
                    ComplianceEngine._finding(
                        rule_id=f"SIGNATURE_{element.upper()}_LAYOUT",
                        category="LAYOUT_VALIDATION",
                        severity="MEDIUM",
                        status=(
                            "PASSED"
                            if actual_position == expected_position
                            else "FAILED"
                        ),
                        expected=expected_position,
                        actual=actual_position,
                        message=(
                            f"{config.get('label', element)} signature is in the expected layout zone"
                            if actual_position == expected_position
                            else f"{config.get('label', element)} signature is not in the expected layout zone"
                        )
                    )
                )

        return findings

    @staticmethod
    def _validate_document_order(template_schema, report_model):
        expected = template_schema.get("document_order", [])
        actual = report_model.get("detected_document_order", [])
        actual_expected = [
            component
            for component in actual
            if component in expected
        ]
        expected_present = [
            component
            for component in expected
            if component in actual_expected
        ]

        if not expected:
            return []

        return [
            ComplianceEngine._finding(
                rule_id="DOCUMENT_COMPONENT_ORDER",
                category="DOCUMENT_STRUCTURE",
                severity="MEDIUM",
                status=(
                    "PASSED"
                    if actual_expected == expected_present
                    else "FAILED"
                ),
                expected=expected,
                actual=actual_expected,
                message=(
                    "Document components appear in the expected order"
                    if actual_expected == expected_present
                    else "Document components do not appear in the expected order"
                )
            )
        ]

    @staticmethod
    def _finding(
        rule_id,
        category,
        severity,
        status,
        expected,
        actual,
        message
    ):
        return {
            "rule_id": rule_id,
            "category": category,
            "severity": severity,
            "status": status,
            "expected": expected,
            "actual": actual,
            "message": message,
        }

    @staticmethod
    def _has_value(value):
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return bool(value)
        return True

    @staticmethod
    def _looks_like_report_model(value: Any):
        return (
            isinstance(value, dict)
            and "event_information_table" in value
            and "components" not in value
        )

    @staticmethod
    def _category_issues(findings, category):
        return [
            finding
            for finding in findings
            if finding.get("category") == category
        ]
