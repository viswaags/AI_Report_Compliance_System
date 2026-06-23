import os
import re

import pdfplumber
from docx import Document

from app.models.canonical_template_schema import (
    ALLOWED_SUMMARY_FORMATS,
    canonical_component_skeleton,
)
from app.services.document_parser import DocumentParser
from app.services.template_schema_generator import TemplateSchemaGenerator


class TemplateAnalyzer:

    OPTIONAL_MARKER_PATTERN = re.compile(r"\(?\s*optional\s*\)?", re.IGNORECASE)
    CONTACT_PATTERN = re.compile(
        r"(@|\b\d{6}\b|\b(?:phone|email|www|http)\b)",
        re.IGNORECASE
    )
    IMAGE_PATTERN = re.compile(
        r"\b(image|photo|figure|caption)\b",
        re.IGNORECASE
    )
    SUMMARY_PATTERN = re.compile(
        r"\b(overview|summary|paragraph|bullet|numbered|outcomes?|achievements?)\b",
        re.IGNORECASE
    )

    @staticmethod
    def analyze_file(
        file_path,
        version
    ):
        parsed_data = TemplateAnalyzer._parse_template(file_path)
        return TemplateAnalyzer.analyze_parsed_data(
            parsed_data,
            version
        )

    @staticmethod
    def analyze_parsed_data(
        parsed_data,
        version
    ):
        text = parsed_data.get("text", "")
        lines = [
            TemplateAnalyzer._clean_text(line)
            for line in text.splitlines()
            if TemplateAnalyzer._clean_text(line)
        ]

        components = TemplateAnalyzer._extract_components(
            lines,
            parsed_data
        )

        return TemplateSchemaGenerator.generate(
            version=version,
            components=components,
            page_constraints={
                "max_pages": parsed_data.get("page_count")
            }
        )

    @staticmethod
    def _parse_template(file_path):
        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".pdf":
            parsed_data = DocumentParser.parse_pdf(file_path)
            parsed_data["tables"] = TemplateAnalyzer._extract_pdf_tables(file_path)
            return parsed_data

        if extension == ".docx":
            parsed_data = DocumentParser.parse_docx(file_path)
            parsed_data["tables"] = TemplateAnalyzer._extract_docx_tables(file_path)
            return parsed_data

        raise ValueError("Unsupported template file type")

    @staticmethod
    def _extract_components(lines, parsed_data):
        components = canonical_component_skeleton()
        tables = parsed_data.get("tables", [])

        components["header"] = TemplateAnalyzer._extract_header_component(
            lines,
            parsed_data
        )
        components["report_title"] = TemplateAnalyzer._extract_title_component(
            lines,
            parsed_data
        )
        components["event_information_table"] = (
            TemplateAnalyzer._extract_event_information_table(tables)
        )
        components["summary"] = TemplateAnalyzer._extract_summary_component(lines)
        components["images"] = TemplateAnalyzer._extract_images_component(
            lines,
            parsed_data
        )
        components["signatures"] = TemplateAnalyzer._extract_signatures_component(
            lines,
            parsed_data
        )

        return components

    @staticmethod
    def _extract_header_component(lines, parsed_data):
        header_lines = TemplateAnalyzer._header_lines(lines, parsed_data)
        elements = {}

        image_count = parsed_data.get("image_count", 0)
        if image_count:
            elements["left_logo"] = {
                "required": True,
                "position": "top_left",
            }

        if header_lines:
            elements["institution_info"] = {
                "required": True,
                "position": "top_center",
                "metadata": header_lines,
            }

        if image_count > 1:
            elements["right_logo"] = {
                "required": False,
                "position": "top_right",
            }

        return {
            "required": True,
            "elements": elements,
        }

    @staticmethod
    def _extract_title_component(lines, parsed_data):
        title_line = TemplateAnalyzer._find_title_line(lines)
        component = {
            "required": True,
            "position": "center",
        }

        if title_line:
            component["label"] = title_line
            location = TemplateAnalyzer._find_text_location(
                title_line,
                parsed_data.get("layout", [])
            )
            if location:
                component["detected_position"] = (
                    TemplateAnalyzer._position_from_location(location)
                )

        return component

    @staticmethod
    def _extract_event_information_table(tables):
        table = TemplateAnalyzer._select_event_information_table(tables)
        fields = {}
        field_order = []
        optional_fields = []

        if table:
            for row_index, row in enumerate(table.get("rows", [])):
                label = TemplateAnalyzer._label_from_table_row(row)
                if not label:
                    continue

                required = not TemplateAnalyzer.OPTIONAL_MARKER_PATTERN.search(label)
                clean_label = TemplateAnalyzer._clean_field_label(label)
                if not clean_label:
                    continue

                key = TemplateSchemaGenerator.normalize_key(clean_label)
                if key in fields:
                    continue

                field_order.append(key)
                fields[key] = {
                    "label": clean_label,
                    "labels": [clean_label],
                    "required": required,
                    "row_order": row_index,
                }

                if not required:
                    optional_fields.append(key)

        required_order = [
            key
            for key in field_order
            if key not in optional_fields
        ]

        return {
            "required": True,
            "table_required": True,
            "table_present_in_template": bool(table),
            "field_order": field_order,
            "fields": fields,
            "optional_fields": optional_fields,
            "additional_fields": {
                "allowed": True,
                "must_appear_after": required_order[-1] if required_order else None,
            },
        }

    @staticmethod
    def _extract_summary_component(lines):
        component = {
            "required": any(TemplateAnalyzer.SUMMARY_PATTERN.search(line) for line in lines),
            "allowed_formats": list(ALLOWED_SUMMARY_FORMATS),
        }

        detected_formats = []
        lower_text = "\n".join(lines).lower()
        if "paragraph" in lower_text:
            detected_formats.append("paragraph")
        if "bullet" in lower_text:
            detected_formats.append("bullets")
        if "numbered" in lower_text:
            detected_formats.append("numbered")

        if detected_formats:
            component["allowed_formats"] = detected_formats

        return component

    @staticmethod
    def _extract_images_component(lines, parsed_data):
        image_lines = [
            line
            for line in lines
            if TemplateAnalyzer.IMAGE_PATTERN.search(line)
        ]

        image_count = parsed_data.get(
            "image_count",
            0
        )

        caption_required = any(
            re.search(r"\b(caption|figure)\b", line, re.IGNORECASE)
            for line in image_lines
        )

        if not caption_required:

            caption_required = any(
                "image" in line.lower()
                for line in lines
            )

        required = (
            caption_required
            or bool(image_lines)
            or image_count > 0
        )

        min_images, max_images = TemplateAnalyzer._extract_image_bounds(
            image_lines,
            required
        )

        return {
            "required": required,
            "min_images": min_images,
            "max_images": max_images,
            "caption_required": caption_required,
        }

    @staticmethod
    def _extract_signatures_component(lines, parsed_data):
        elements = {}
        signature_labels = TemplateAnalyzer._signature_labels_from_layout(
            parsed_data.get("layout", [])
        )

        if not signature_labels:
            signature_labels = TemplateAnalyzer._signature_labels_from_lines(lines)

        for index, signature in enumerate(signature_labels):
            key = TemplateSchemaGenerator.normalize_key(signature["label"])
            if key in elements:
                continue

            elements[key] = {
                "label": signature["label"],
                "required": True,
                "position": signature.get("position") or (
                    "bottom_left" if index == 0 else "bottom_right"
                ),
            }

        return {
            "required": True,
            "elements": elements,
        }

    @staticmethod
    def _extract_pdf_tables(file_path):
        tables = []

        with pdfplumber.open(file_path) as pdf:
            for page_index, page in enumerate(pdf.pages):
                for table_index, rows in enumerate(page.extract_tables() or []):
                    normalized_rows = [
                        [
                            TemplateAnalyzer._clean_text(cell or "")
                            for cell in row
                        ]
                        for row in rows
                    ]
                    tables.append({
                        "page_number": page_index + 1,
                        "table_index": table_index,
                        "rows": normalized_rows,
                    })

        return tables

    @staticmethod
    def _extract_docx_tables(file_path):
        document = Document(file_path)
        tables = []

        for table_index, table in enumerate(document.tables):
            rows = []
            for row in table.rows:
                rows.append([
                    TemplateAnalyzer._clean_text(cell.text)
                    for cell in row.cells
                ])
            tables.append({
                "table_index": table_index,
                "rows": rows,
            })

        return tables

    @staticmethod
    def _select_event_information_table(tables):
        candidates = []

        for table in tables:
            rows = table.get("rows", [])
            label_rows = [
                row
                for row in rows
                if TemplateAnalyzer._label_from_table_row(row)
            ]

            if len(label_rows) >= 2:
                candidates.append((len(label_rows), table))

        if not candidates:
            return None

        return sorted(candidates, key=lambda item: item[0], reverse=True)[0][1]

    @staticmethod
    def _label_from_table_row(row):
        if not row:
            return None

        for cell in row:
            cleaned = TemplateAnalyzer._clean_text(cell)
            if cleaned:
                return cleaned

        return None

    @staticmethod
    def _clean_field_label(label):
        label = TemplateAnalyzer.OPTIONAL_MARKER_PATTERN.sub("", label)
        label = re.sub(r"\s+", " ", label).strip(" :-")
        return label

    @staticmethod
    def _header_lines(lines, parsed_data):
        title_line = TemplateAnalyzer._find_title_line(lines)
        header_lines = []

        for line in lines:
            if line == title_line:
                break

            if TemplateAnalyzer.IMAGE_PATTERN.search(line):
                continue

            if line not in header_lines:
                header_lines.append(line)

        if header_lines:
            return header_lines

        for page in parsed_data.get("layout", []):
            page_height = page.get("height") or 1
            for block in page.get("text_blocks", []):
                center_y = (
                    (block.get("y0", 0) + block.get("y1", 0)) / 2
                ) / page_height
                if center_y > 0.2:
                    continue
                for line in TemplateAnalyzer._lines_from_text(block.get("text", "")):
                    if line not in header_lines:
                        header_lines.append(line)

        return header_lines

    @staticmethod
    def _find_title_line(lines):
        for line in lines:
            if re.search(r"\breport\s+title\b", line, re.IGNORECASE):
                return line

        for line in lines:
            if (
                not TemplateAnalyzer.CONTACT_PATTERN.search(line)
                and len(line.split()) <= 8
            ):
                return line

        return None

    @staticmethod
    def _signature_labels_from_layout(pages):
        labels = []

        for page in pages:
            page_width = page.get("width") or 1
            page_height = page.get("height") or 1

            for block in page.get("text_blocks", []):
                center_y = (
                    (block.get("y0", 0) + block.get("y1", 0)) / 2
                ) / page_height
                if center_y < 0.75:
                    continue

                center_x = (
                    (block.get("x0", 0) + block.get("x1", 0)) / 2
                ) / page_width
                position = "bottom_left" if center_x < 0.5 else "bottom_right"

                block_labels = TemplateAnalyzer._split_signature_text(
                    block.get("text", "")
                )
                for index, label in enumerate(block_labels):
                    label_position = position
                    if len(block_labels) > 1:
                        label_position = (
                            "bottom_left" if index == 0 else "bottom_right"
                        )
                    labels.append({
                        "label": label,
                        "position": label_position,
                    })

        if len(labels) == 1:
            split_labels = TemplateAnalyzer._split_signature_text(labels[0]["label"])
            if len(split_labels) > 1:
                return [
                    {
                        "label": label,
                        "position": "bottom_left" if index == 0 else "bottom_right",
                    }
                    for index, label in enumerate(split_labels)
                ]

        return labels

    @staticmethod
    def _signature_labels_from_lines(lines):
        if not lines:
            return []

        tail_text = "\n".join(lines[-4:])
        return [
            {
                "label": label,
                "position": "bottom_left" if index == 0 else "bottom_right",
            }
            for index, label in enumerate(
                TemplateAnalyzer._split_signature_text(tail_text)
            )
        ]

    @staticmethod
    def _split_signature_text(text):
        cleaned = re.sub(r"[\u200b\u200c\u200d\ufeff]", "    ", str(text or ""))
        candidates = []

        for line in re.split(r"\n|\s{4,}", cleaned):
            line = TemplateAnalyzer._clean_text(line)
            if not line:
                continue
            if len(line.split()) > 5:
                continue
            if TemplateAnalyzer.IMAGE_PATTERN.search(line):
                continue
            if TemplateAnalyzer.SUMMARY_PATTERN.search(line):
                continue
            candidates.append(line)

        return candidates

    @staticmethod
    def _extract_image_bounds(image_lines, required):
        numbers = []

        for line in image_lines:
            numbers.extend(
                int(match)
                for match in re.findall(r"\b\d+\b", line)
            )

        if numbers:
            return min(numbers), max(numbers)

        if required:
            return 1, 2

        return 0, None

    @staticmethod
    def _find_text_location(value, pages):
        if not value:
            return None

        search_value = re.sub(r"\s+", " ", value).strip().lower()

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
    def _position_from_location(location):
        page_width = location.get("page_width") or 1
        page_height = location.get("page_height") or 1
        center_x = location.get("center_x", 0) / page_width
        center_y = location.get("center_y", 0) / page_height

        if center_y < 0.25:
            if center_x < 0.33:
                return "top_left"
            if center_x > 0.67:
                return "top_right"
            return "top_center"

        if center_y > 0.75:
            return "bottom_left" if center_x < 0.5 else "bottom_right"

        return "center"

    @staticmethod
    def _lines_from_text(text):
        return [
            TemplateAnalyzer._clean_text(line)
            for line in text.splitlines()
            if TemplateAnalyzer._clean_text(line)
        ]

    @staticmethod
    def _clean_text(value):
        value = re.sub(r"[\u200b\u200c\u200d\ufeff]", " ", str(value or ""))
        return re.sub(r"\s+", " ", value).strip()
