import re
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
    def _validate_page_count(
        template_schema,
        report_model
    ):
        max_pages = (
            template_schema
            .get("page_constraints", {})
            .get("max_pages")
        )

        if max_pages is None:
            return []

        actual = report_model.get("page_count")

        if actual is None:
            return []

        return [
            ComplianceEngine._finding(
                rule_id="PAGE_LIMIT",
                category="PAGE_VALIDATION",
                severity="HIGH",
                status=(
                    "PASSED"
                    if actual <= max_pages
                    else "FAILED"
                ),
                expected=f"Maximum {max_pages} page(s)",
                actual=f"{actual} page(s)",
                message=(
                    f"Report page count is within limit"
                    if actual <= max_pages
                    else f"Report exceeds maximum page limit"
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
                ),
            )
        )

        for element, config in header_schema.get("elements", {}).items():

            model_element = header_model.get("elements", {}).get(element, {})

            # ---------------------------------------------------------
            # Required element validation
            # ---------------------------------------------------------

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
                        ),
                    )
                )

            # ---------------------------------------------------------
            # Layout validation
            # ---------------------------------------------------------

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
                        ),
                    )
                )

            # ---------------------------------------------------------
            # Institution metadata validation
            # ---------------------------------------------------------

            if (
                element == "institution_info"
                and model_element.get("present")
            ):

                expected_metadata = config.get("metadata", [])
                actual_metadata = model_element.get("metadata", [])

                actual_text = " ".join(actual_metadata).lower()

                metadata_valid = all(
                    expected.lower() in actual_text
                    for expected in expected_metadata
                )

                findings.append(

                    ComplianceEngine._finding(

                        rule_id="HEADER_INSTITUTION_METADATA",

                        category="DOCUMENT_STRUCTURE",

                        severity="MEDIUM",

                        status=(
                            "PASSED"
                            if metadata_valid
                            else "FAILED"
                        ),

                        expected=expected_metadata,

                        actual=actual_metadata,

                        message=(
                            "Institution information matches the template"
                            if metadata_valid
                            else "Institution information differs from the template"
                        ),
                    )
                )

        return findings

    @staticmethod
    def _validate_report_title(title_schema, title_model):

        if not title_schema:
            return []

        findings = []

        required = title_schema.get("required", False)
        present = title_model.get("present", False)

        findings.append(

            ComplianceEngine._finding(

                rule_id="REPORT_TITLE_EXISTS",

                category="DOCUMENT_STRUCTURE",

                severity="HIGH",

                status=(
                    "PASSED"
                    if present or not required
                    else "FAILED"
                ),

                expected=(
                    "Report title present"
                    if required
                    else "Report title optional"
                ),

                actual=title_model.get("text") or "Missing",

                message=(
                    "Report title is present"
                    if present or not required
                    else "Required report title is missing"
                ),
            )
        )

        title_text = title_model.get("text", "")

        has_content = bool(str(title_text).strip())

        findings.append(

            ComplianceEngine._finding(

                rule_id="REPORT_TITLE_CONTENT",

                category="DOCUMENT_STRUCTURE",

                severity="HIGH",

                status=(
                    "PASSED"
                    if has_content
                    else "FAILED"
                ),

                expected="Report title contains text",

                actual=title_text,

                message=(
                    "Report title contains text"
                    if has_content
                    else "Report title is empty"
                ),
            )
        )

        expected_position = (
            title_schema.get("detected_position")
            or title_schema.get("position")
        )

        actual_position = title_model.get("zone")

        if expected_position:

            valid_positions = {
                expected_position,
            }

            if expected_position == "top_center":
                valid_positions.update({
                    "center",
                    "top_left",
                    "top_right",
                })

            elif expected_position == "center":
                valid_positions.update({
                    "top_center",
                })

            findings.append(

                ComplianceEngine._finding(

                    rule_id="REPORT_TITLE_POSITION",

                    category="LAYOUT_VALIDATION",

                    severity="MEDIUM",

                    status=(
                        "PASSED"
                        if actual_position in valid_positions
                        else "FAILED"
                    ),

                    expected=expected_position,

                    actual=actual_position,

                    message=(
                        "Report title is in the expected position"
                        if actual_position in valid_positions
                        else "Report title is not in the expected position"
                    ),
                )
            )

        return findings

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

            value = ComplianceEngine._normalize_field_value(
                fields.get(field)
            )
            has_value = ComplianceEngine._has_value(value)
            present = has_value
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

            expected_type = config.get("expected_type", "string")

            if not has_value:
                continue

            type_valid = True

            if expected_type == "integer":

                text = str(value).strip()

                match = re.search(r"\d+", text)

                type_valid = match is not None

            elif expected_type == "datetime":

                text = str(value).strip()

                type_valid = (
                    re.search(
                        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
                        text,
                        re.IGNORECASE,
                    )
                    or
                    re.search(
                        r"\b\d{1,2}\s+"
                        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
                        r"|january|february|march|april|june|july|august|"
                        r"september|october|november|december)"
                        r"\s+\d{4}",
                        text,
                        re.IGNORECASE,
                    )
                )

                type_valid = bool(type_valid)

            elif expected_type == "string":

                type_valid = bool(str(value).strip())

            findings.append(
                ComplianceEngine._finding(
                    rule_id=f"EVENT_TABLE_FIELD_{field.upper()}_TYPE",
                    category="FIELD_VALIDATION",
                    severity="MEDIUM",
                    status="PASSED" if type_valid else "FAILED",
                    expected=expected_type,
                    actual=value,
                    message=(
                        f"{config.get('label', field)} has the expected data type"
                        if type_valid
                        else f"{config.get('label', field)} does not match the expected data type"
                    ),
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
                ),
            )
        )

        content = summary_model.get("content", "")

        has_content = bool(str(content).strip())

        findings.append(

            ComplianceEngine._finding(

                rule_id="SUMMARY_CONTENT",

                category="DOCUMENT_STRUCTURE",

                severity="HIGH",

                status=(
                    "PASSED"
                    if has_content
                    else "FAILED"
                ),

                expected="Summary contains content",

                actual=content,

                message=(
                    "Summary contains content"
                    if has_content
                    else "Summary is empty"
                ),
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
                        "Summary format is allowed"
                        if actual_format in allowed_formats
                        else "Summary format is not allowed"
                    ),
                )
            )

        expected_position = summary_schema.get("position", {})

        actual_after = summary_model.get("after")
        actual_before = summary_model.get("before")

        expected_after = expected_position.get("after")
        expected_before = expected_position.get("before")

        position_valid = (
            actual_after == expected_after
            and (
                actual_before == expected_before
                or (
                    expected_before == "images"
                    and actual_before == "signatures"
                )
            )
        )

        findings.append(

            ComplianceEngine._finding(

                rule_id="SUMMARY_POSITION",

                category="LAYOUT_VALIDATION",

                severity="MEDIUM",

                status=(
                    "PASSED"
                    if position_valid
                    else "FAILED"
                ),

                expected=expected_position,

                actual={
                    "after": actual_after,
                    "before": actual_before,
                },

                message=(
                    "Summary is in the expected position"
                    if position_valid
                    else "Summary is not in the expected position"
                ),
            )
        )

        return findings

    @staticmethod
    def _validate_images(images_schema, images_model):
        if not images_schema:
            return []

        findings = []

        items = images_model.get("items", [])

        '''header_images = [
            image
            for image in items
            if image.get("is_header")
        ]'''

        content_images = [
            image
            for image in items
            if not image.get("is_header")
        ]

        header_image_count = images_model["header_count"]
        content_image_count = images_model["content_count"]

        # ---------------------------------------------------------
        # Validate content image count
        # ---------------------------------------------------------

        min_images = images_schema.get("min_images", 0)
        max_images = images_schema.get("max_images")

        valid_min = content_image_count >= min_images
        valid_max = (
            max_images is None
            or content_image_count <= max_images
        )

        findings.append(
            ComplianceEngine._finding(
                rule_id="IMAGE_COUNT",
                category="IMAGE_VALIDATION",
                severity="HIGH",
                status=(
                    "PASSED"
                    if valid_min and valid_max
                    else "FAILED"
                ),
                expected={
                    "min_images": min_images,
                    "max_images": max_images,
                },
                actual=content_image_count,
                message=(
                    "Content image count satisfies template requirements"
                    if valid_min and valid_max
                    else "Content image count does not satisfy template requirements"
                ),
            )
        )

        # ---------------------------------------------------------
        # Validate header image count
        # ---------------------------------------------------------

        expected_header = images_schema.get("header_image_count")

        if expected_header is not None:

            findings.append(

                ComplianceEngine._finding(

                    rule_id="HEADER_IMAGE_COUNT",

                    category="IMAGE_VALIDATION",

                    severity="MEDIUM",

                    status=(
                        "PASSED"
                        if header_image_count == expected_header
                        else "FAILED"
                    ),

                    expected=expected_header,

                    actual=header_image_count,

                    message=(
                        "Header image count matches template"
                        if header_image_count == expected_header
                        else "Header image count differs from template"
                    ),
                )
            )

        # ---------------------------------------------------------
        # Validate captions
        # ---------------------------------------------------------

        if images_schema.get("caption_required", False):

            '''caption_present = (
                len(content_images) > 0
                and all(
                    image.get("caption")
                    for image in content_images
                )
            )'''
            unique_captions = {
                image.get("caption").strip()
                for image in content_images
                if image.get("caption") and image.get("caption").strip()
            }

            caption_present = (
                content_image_count == 0
                or len(unique_captions) >= 1
            )

            if content_image_count == 0:
                caption_present = True

            elif len(unique_captions) >= 1:
                caption_present = True

            findings.append(

                ComplianceEngine._finding(

                    rule_id="IMAGE_CAPTIONS",

                    category="IMAGE_VALIDATION",

                    severity="MEDIUM",

                    status=(
                        "PASSED"
                        if caption_present
                        else "FAILED"
                    ),

                    expected=(
                        "Every content image must be associated with at least one caption. "
                        "A caption may describe multiple images."
                    ),

                    actual=caption_present,

                    message=(
                        "Content images are associated with captions"
                        if caption_present
                        else "No caption could be associated with the content images"
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

            present = model_element.get("present", False)

            # ---------------------------------------------------------
            # Signature Exists
            # ---------------------------------------------------------

            if config.get("required", True):

                findings.append(

                    ComplianceEngine._finding(

                        rule_id=f"SIGNATURE_{element.upper()}_EXISTS",

                        category="SIGNATURE_VALIDATION",

                        severity="HIGH",

                        status=(
                            "PASSED"
                            if present
                            else "FAILED"
                        ),

                        expected=f"{config.get('label', element)} signature present",

                        actual=(
                            "Present"
                            if present
                            else "Missing"
                        ),

                        message=(
                            f"{config.get('label', element)} signature is present"
                            if present
                            else f"Required signature '{config.get('label', element)}' is missing"
                        ),
                    )
                )

            # ---------------------------------------------------------
            # Signature Position
            # ---------------------------------------------------------

            expected_position = config.get("position")

            actual_position = (
                model_element.get("zone")
                or "unknown"
            )

            if expected_position and present:

                findings.append(

                    ComplianceEngine._finding(

                        rule_id=f"SIGNATURE_{element.upper()}_POSITION",

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
                            f"{config.get('label', element)} signature is in the expected position"
                            if actual_position == expected_position
                            else f"{config.get('label', element)} signature is not in the expected position"
                        ),
                    )
                )

            # ---------------------------------------------------------
            # Signature Label
            # ---------------------------------------------------------

            expected_aliases = [
                alias.lower()
                for alias in config.get("aliases", [])
            ]

            actual_text = model_element.get("text", "")

            if actual_text is None:
                actual_text = ""

            actual_label = actual_text.strip().lower()

            if present and expected_aliases:

                alias_match = any(
                    alias in actual_label
                    for alias in expected_aliases
                )

                findings.append(

                    ComplianceEngine._finding(

                        rule_id=f"SIGNATURE_{element.upper()}_LABEL",

                        category="SIGNATURE_VALIDATION",

                        severity="LOW",

                        status=(
                            "PASSED"
                            if alias_match
                            else "FAILED"
                        ),

                        expected=config.get("aliases"),

                        actual=model_element.get("text"),

                        message=(
                            "Signature label matches the template"
                            if alias_match
                            else "Signature label differs from the template"
                        ),
                    )
                )

        return findings

    @staticmethod
    def _validate_document_order(template_schema, report_model):

        validation_rules = template_schema.get(
            "validation_rules",
            {}
        )

        if not validation_rules.get(
            "section_order_required",
            False
        ):
            return []

        expected = template_schema.get(
            "document_order",
            []
        )

        actual = report_model.get(
            "detected_document_order",
            []
        )

        if not expected:
            return []

        comparable_actual = [
            component
            for component in actual
            if component in expected
        ]

        expected_present = [
            component
            for component in expected
            if component in comparable_actual
        ]

        order_valid = (
            comparable_actual == expected_present
        )

        return [

            ComplianceEngine._finding(

                rule_id="DOCUMENT_COMPONENT_ORDER",

                category="DOCUMENT_STRUCTURE",

                severity="MEDIUM",

                status=(
                    "PASSED"
                    if order_valid
                    else "FAILED"
                ),

                expected=expected,

                actual=actual,

                message=(
                    "Document components are in the expected order"
                    if order_valid
                    else "Document components are not in the expected order"
                ),
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
    
    @staticmethod
    def _normalize_field_value(value):

        if value is None:
            return None

        if isinstance(value, str):

            value = (
                value
                .replace("\n", " ")
                .replace("\t", " ")
                .strip()
            )

            value = re.sub(r"\s+", " ", value)

            return value

        return value