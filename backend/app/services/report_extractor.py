import re
from typing import Any


class ReportExtractor:

    @staticmethod
    def extract(
        parsed_data,
        template_schema
    ):
        text = parsed_data.get("text", "")
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        field_configs = ReportExtractor._collect_field_configs(template_schema)
        section_configs = ReportExtractor._collect_section_configs(template_schema)

        fields = {}
        field_locations = {}

        for field, config in field_configs.items():
            value = ReportExtractor._extract_field_value(field, config, text, lines)
            fields[field] = value

            if value:
                location = ReportExtractor._find_text_location(
                    str(value),
                    parsed_data.get("layout", [])
                )
                if location:
                    field_locations[field] = location

        sections = ReportExtractor._extract_sections(
            section_configs,
            text,
            lines,
            parsed_data.get("layout", [])
        )

        captions = ReportExtractor._extract_image_captions(
            text,
            template_schema
        )

        summary_config = ReportExtractor._as_dict(
            template_schema.get("summary", {})
        )
        summary_section = sections.get("summary", {})

        report_json = {
            "fields": fields,
            "field_locations": field_locations,
            "sections": sections,
            "summary": {
                "present": bool(summary_section.get("present")) or len(text.strip()) > 0,
                "type": (
                    summary_config.get("type")
                    or summary_config.get("summary_type")
                    or ReportExtractor._infer_summary_type(text)
                ),
                "content": summary_section.get("content") or text[:500]
            },
            "images": {
                "count": parsed_data.get("image_count", 0),
                "captions": captions,
                "caption_present": len(captions) > 0
            },
            "layout": {
                "page_count": parsed_data.get("page_count", 1),
                "pages": parsed_data.get("layout", [])
            }
        }

        ReportExtractor._populate_legacy_sections(
            report_json,
            template_schema
        )

        return report_json

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
                if field in {"required_fields", "layout_rules", "sections"}:
                    continue

                if isinstance(config, dict):
                    fields.setdefault(field, config)

        for field, config in ReportExtractor._items_from_schema_node(
            template_schema.get("fields")
        ):
            fields[field] = config

        for _, section_config in ReportExtractor._items_from_schema_node(
            template_schema.get("sections")
        ):
            for field, config in ReportExtractor._items_from_schema_node(
                section_config.get("fields") if isinstance(section_config, dict) else None
            ):
                fields.setdefault(field, config)

        return fields

    @staticmethod
    def _collect_section_configs(template_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
        sections = {}

        for index, section in enumerate(template_schema.get("required_sections", [])):
            sections[section] = {
                "required": True,
                "order": index
            }

        for section, config in ReportExtractor._items_from_schema_node(
            template_schema.get("sections")
        ):
            sections[section] = config

        for section, config in template_schema.items():
            if isinstance(config, dict) and config.get("section"):
                sections.setdefault(section, config)

        if "summary" in template_schema:
            sections.setdefault("summary", ReportExtractor._as_dict(template_schema["summary"]))

        return sections

    @staticmethod
    def _items_from_schema_node(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key, ReportExtractor._as_dict(value)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                if isinstance(item, str):
                    yield item, {"order": index}
                elif isinstance(item, dict):
                    key = (
                        item.get("key")
                        or item.get("name")
                        or item.get("id")
                        or item.get("field")
                        or item.get("section")
                    )
                    if key:
                        yield key, item

    @staticmethod
    def _as_dict(value):
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _extract_field_value(field, config, text, lines):
        labels = ReportExtractor._labels_for(field, config)

        for label in labels:
            pattern = re.compile(
                rf"(?im)^\s*{re.escape(label)}\s*(?:[:\-|]\s*|\s{{2,}})(.+?)\s*$"
            )
            match = pattern.search(text)
            if match:
                return match.group(1).strip()

        return None

    @staticmethod
    def _labels_for(key, config):
        labels = []

        for config_key in ["label", "display_name", "title", "name"]:
            value = config.get(config_key)
            if isinstance(value, str):
                labels.append(value)

        for config_key in ["labels", "aliases"]:
            values = config.get(config_key, [])
            if isinstance(values, list):
                labels.extend(value for value in values if isinstance(value, str))

        labels.append(key.replace("_", " ").title())
        labels.append(key.replace("_", " "))

        seen = set()
        unique_labels = []
        for label in labels:
            normalized = label.lower()
            if normalized not in seen:
                seen.add(normalized)
                unique_labels.append(label)

        return unique_labels

    @staticmethod
    def _extract_sections(section_configs, text, lines, pages):
        headings = []

        for section, config in section_configs.items():
            labels = ReportExtractor._labels_for(section, config)
            for line_index, line in enumerate(lines):
                if ReportExtractor._line_matches_label(line, labels):
                    headings.append({
                        "section": section,
                        "line_index": line_index,
                        "line": line
                    })
                    break

        headings.sort(key=lambda item: item["line_index"])

        sections = {}
        for index, heading in enumerate(headings):
            next_index = (
                headings[index + 1]["line_index"]
                if index + 1 < len(headings)
                else len(lines)
            )
            content_lines = lines[heading["line_index"] + 1:next_index]
            sections[heading["section"]] = {
                "present": True,
                "heading": heading["line"],
                "content": "\n".join(content_lines).strip(),
                "order_index": index
            }

            location = ReportExtractor._find_text_location(heading["line"], pages)
            if location:
                sections[heading["section"]]["location"] = location

        for section in section_configs:
            sections.setdefault(
                section,
                {
                    "present": False,
                    "content": None,
                    "order_index": None
                }
            )

        return sections

    @staticmethod
    def _line_matches_label(line, labels):
        normalized_line = re.sub(r"\s+", " ", line).strip().lower()
        for label in labels:
            normalized_label = re.sub(r"\s+", " ", label).strip().lower()
            if normalized_line == normalized_label:
                return True
        return False

    @staticmethod
    def _extract_image_captions(text, template_schema):
        image_rules = ReportExtractor._as_dict(template_schema.get("images", {}))
        patterns = image_rules.get("caption_patterns", [])

        if isinstance(patterns, str):
            patterns = [patterns]

        if not patterns:
            patterns = [
                r"(?im)^\s*(?:caption|fig(?:ure)?|image|photo)\s*[\d.:-]*\s+(.+?)\s*$"
            ]

        captions = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                caption = match.group(1).strip() if match.groups() else match.group(0).strip()
                if caption and caption not in captions:
                    captions.append(caption)

        return captions

    @staticmethod
    def _find_text_location(value, pages):
        search_value = re.sub(r"\s+", " ", value).strip().lower()

        if not search_value:
            return None

        for page in pages:
            page_width = page.get("width")
            page_height = page.get("height")

            for block in page.get("text_blocks", []):
                block_text = re.sub(
                    r"\s+",
                    " ",
                    block.get("text", "")
                ).strip().lower()

                if search_value not in block_text:
                    continue

                x0 = block.get("x0", 0)
                y0 = block.get("y0", 0)
                x1 = block.get("x1", x0)
                y1 = block.get("y1", y0)

                return {
                    "page_number": page.get("page_number"),
                    "page_width": page_width,
                    "page_height": page_height,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "center_x": (x0 + x1) / 2,
                    "center_y": (y0 + y1) / 2
                }

        return None

    @staticmethod
    def _infer_summary_type(text):
        lower_text = text.lower()

        if re.search(r"\b(bullets?|points?)\b", lower_text):
            return "bullet"

        if re.search(r"\b(table|tabular)\b", lower_text):
            return "table"

        return "narrative"

    @staticmethod
    def _populate_legacy_sections(report_json, template_schema):
        fields = report_json["fields"]

        report_json["header"] = {}
        for field in template_schema.get("header", {}):
            report_json["header"][field] = fields.get(field)

        if "college_logo" in template_schema.get("header", {}):
            report_json["header"]["college_logo"] = report_json["images"]["count"] > 0

        report_json["metadata_table"] = {}
        for field in template_schema.get("metadata_table", {}).get("required_fields", []):
            report_json["metadata_table"][field] = fields.get(field)

        report_json["signature_sections"] = {}
        for signature in template_schema.get("signature_sections", {}):
            report_json["signature_sections"][signature] = bool(
                report_json["sections"].get(signature, {}).get("present")
            )
