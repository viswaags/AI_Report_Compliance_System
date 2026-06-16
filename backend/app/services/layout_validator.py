class LayoutValidator:

    @staticmethod
    def validate(
        report_data,
        template_schema
    ):
        layout_rules = template_schema.get("layout_rules", {})
        zones = (
            layout_rules.get("zones")
            or template_schema.get("layout", {}).get("zones", {})
        )
        field_rules = LayoutValidator._collect_field_layout_rules(template_schema)

        if not field_rules:
            return {
                "issues": [],
                "total_checks": 0,
                "passed_checks": 0
            }

        issues = []
        total_checks = 0
        passed_checks = 0

        for field, rule in field_rules.items():
            zone_name = rule.get("zone") or rule.get("position")

            if not zone_name:
                continue

            total_checks += 1
            location = report_data.get("field_locations", {}).get(field)

            if not location:
                issues.append({
                    "type": "layout_location_missing",
                    "field": field,
                    "severity": rule.get("severity", "low"),
                    "message": f"{LayoutValidator._label(field)} location could not be determined"
                })
                continue

            zone = zones.get(zone_name) if isinstance(zones, dict) else None

            if not zone:
                issues.append({
                    "type": "layout_zone_missing",
                    "field": field,
                    "severity": "medium",
                    "message": f"Layout zone '{zone_name}' is not defined in template schema",
                    "zone": zone_name
                })
                continue

            if LayoutValidator._location_matches_rule(location, zone, rule):
                passed_checks += 1
            else:
                issues.append({
                    "type": "layout_mismatch",
                    "field": field,
                    "severity": rule.get("severity", "medium"),
                    "message": f"{LayoutValidator._label(field)} is outside expected layout zone",
                    "zone": zone_name,
                    "location": location
                })

        return {
            "issues": issues,
            "total_checks": total_checks,
            "passed_checks": passed_checks
        }

    @staticmethod
    def validate_position(
        text,
        position,
        pages
    ):
        report_data = {
            "field_locations": {
                "text": LayoutValidator._find_text_location(text, pages)
            }
        }
        template_schema = {
            "fields": {
                "text": {
                    "layout": {
                        "zone": position
                    }
                }
            },
            "layout_rules": {
                "zones": {}
            }
        }

        result = LayoutValidator.validate(report_data, template_schema)
        return result["total_checks"] > 0 and not result["issues"]

    @staticmethod
    def _collect_field_layout_rules(template_schema):
        field_rules = {}

        for field, config in LayoutValidator._field_config_items(template_schema):
            if not isinstance(config, dict):
                continue

            layout = config.get("layout", {})

            if isinstance(layout, dict) and (layout.get("zone") or layout.get("position")):
                field_rules[field] = layout
            elif config.get("zone") or config.get("position"):
                field_rules[field] = config

        return field_rules

    @staticmethod
    def _field_config_items(template_schema):
        legacy_field_containers = {
            "header",
            "metadata_table",
        }

        for container_name in legacy_field_containers:
            section_config = template_schema.get(container_name, {})
            if isinstance(section_config, dict):
                for field, config in section_config.items():
                    if isinstance(config, dict):
                        yield field, config

        signature_sections = template_schema.get("signature_sections", {})
        if isinstance(signature_sections, dict):
            for field, config in signature_sections.items():
                if isinstance(config, dict):
                    yield field, config

        for section_config in template_schema.values():
            if isinstance(section_config, dict) and section_config.get("field_container"):
                for field, config in section_config.items():
                    if isinstance(config, dict):
                        yield field, config

        fields = template_schema.get("fields")
        if isinstance(fields, dict):
            for field, config in fields.items():
                yield field, config
        elif isinstance(fields, list):
            for item in fields:
                if isinstance(item, dict):
                    field = item.get("key") or item.get("name") or item.get("field")
                    if field:
                        yield field, item

    @staticmethod
    def _location_matches_rule(location, zone, rule):
        page = rule.get("page") or zone.get("page")
        if page and location.get("page_number") != page:
            return False

        page_width = location.get("page_width") or 1
        page_height = location.get("page_height") or 1

        center_x = location.get("center_x", 0) / page_width
        center_y = location.get("center_y", 0) / page_height

        x_min, x_max = LayoutValidator._range_from_zone(zone, "x")
        y_min, y_max = LayoutValidator._range_from_zone(zone, "y")

        return x_min <= center_x <= x_max and y_min <= center_y <= y_max

    @staticmethod
    def _range_from_zone(zone, axis):
        range_value = zone.get(f"{axis}_range")

        if isinstance(range_value, list) and len(range_value) == 2:
            return LayoutValidator._normalize(range_value[0]), LayoutValidator._normalize(range_value[1])

        min_value = (
            zone.get(f"{axis}_min")
            if zone.get(f"{axis}_min") is not None
            else zone.get(f"{axis}0")
        )
        max_value = (
            zone.get(f"{axis}_max")
            if zone.get(f"{axis}_max") is not None
            else zone.get(f"{axis}1")
        )

        return (
            LayoutValidator._normalize(0 if min_value is None else min_value),
            LayoutValidator._normalize(1 if max_value is None else max_value)
        )

    @staticmethod
    def _normalize(value):
        value = float(value)
        return value / 100 if value > 1 else value

    @staticmethod
    def _find_text_location(text, pages):
        if not text:
            return None

        search_text = text.strip().lower()
        for page in pages:
            for block in page.get("text_blocks", []):
                if search_text not in block.get("text", "").strip().lower():
                    continue

                x0 = block.get("x0", 0)
                y0 = block.get("y0", 0)
                x1 = block.get("x1", x0)
                y1 = block.get("y1", y0)

                return {
                    "page_number": page.get("page_number"),
                    "page_width": page.get("width"),
                    "page_height": page.get("height"),
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "center_x": (x0 + x1) / 2,
                    "center_y": (y0 + y1) / 2
                }

        return None

    @staticmethod
    def _label(field):
        return field.replace("_", " ").title()
