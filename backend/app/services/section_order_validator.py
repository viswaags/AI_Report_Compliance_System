class SectionOrderValidator:

    @staticmethod
    def validate(
        report_data,
        template_schema
    ):
        expected_order = SectionOrderValidator._expected_order(template_schema)

        if not expected_order:
            return {
                "issues": [],
                "total_checks": 0,
                "passed_checks": 0
            }

        sections = report_data.get("sections", {})
        actual_order = [
            section
            for section, data in sorted(
                sections.items(),
                key=lambda item: (
                    item[1].get("order_index") is None,
                    item[1].get("order_index") or 0
                )
            )
            if data.get("present")
        ]

        total_checks = 1
        passed_checks = 0
        issues = []

        expected_present_order = [
            section
            for section in expected_order
            if sections.get(section, {}).get("present")
        ]

        actual_expected_order = [
            section
            for section in actual_order
            if section in expected_order
        ]

        if actual_expected_order == expected_present_order:
            passed_checks = 1
        else:
            issues.append({
                "type": "section_order",
                "field": "sections",
                "severity": "medium",
                "message": "Section order does not match template schema",
                "expected": expected_order,
                "actual": actual_expected_order
            })

        return {
            "issues": issues,
            "total_checks": total_checks,
            "passed_checks": passed_checks
        }

    @staticmethod
    def _expected_order(template_schema):
        if isinstance(template_schema.get("section_order"), list):
            return template_schema["section_order"]

        sections = template_schema.get("sections")

        if isinstance(sections, list):
            ordered = []
            for item in sections:
                if isinstance(item, str):
                    ordered.append(item)
                elif isinstance(item, dict):
                    key = (
                        item.get("key")
                        or item.get("name")
                        or item.get("id")
                        or item.get("section")
                    )
                    if key:
                        ordered.append(key)
            return ordered

        if isinstance(sections, dict):
            sortable_sections = []
            for section, config in sections.items():
                order = config.get("order") if isinstance(config, dict) else None
                if order is not None:
                    sortable_sections.append((order, section))

            if sortable_sections:
                return [
                    section
                    for _, section in sorted(sortable_sections)
                ]

        return template_schema.get("required_sections", [])
