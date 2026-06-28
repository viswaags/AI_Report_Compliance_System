from __future__ import annotations

import os
import re
from copy import deepcopy
from typing import Optional

import pdfplumber
from docx import Document

from app.models.canonical_template_schema import (
    ALLOWED_SUMMARY_FORMATS,
    canonical_component_skeleton,
)
from app.models.template_metadata import (
    DEFAULT_CAPTION_POSITION,
    DEFAULT_DETECTION_STRATEGY,
    DEFAULT_SUMMARY_POSITION,
    FIELD_ALIASES,
    FIELD_EXPECTED_TYPES,
    FOOTER_ZONES,
    HEADER_ZONES,
    SIGNATURE_ROLE_PATTERN,
    SIGNATURE_KEY_MAPPING, 
    SIGNATURE_POSITIONS
)
from app.services.document_parser import DocumentParser
from app.services.template_schema_generator import TemplateSchemaGenerator

_OPTIONAL_RE = re.compile(r"\(?\s*optional\s*\)?", re.IGNORECASE)
_CONTACT_RE = re.compile(
    r"(@|\b\d{6}\b|\b(?:phone|email|www|http)\b)", re.IGNORECASE
)
_IMAGE_RE = re.compile(r"\b(image|photo|figure|caption)\b", re.IGNORECASE)
_SUMMARY_RE = re.compile(
    r"\b(overview|summary|paragraph|bullet|numbered|outcomes?|achievements?)\b",
    re.IGNORECASE,
)
_REPORT_TITLE_RE = re.compile(r"\breport\s+title\b", re.IGNORECASE)
_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")

_KNOWN_FIELD_ALIASES = FIELD_ALIASES
_FIELD_EXPECTED_TYPES = FIELD_EXPECTED_TYPES
_SIGNATURE_ROLE_RE = SIGNATURE_ROLE_PATTERN
_HEADER_ZONES = HEADER_ZONES
_FOOTER_ZONES = FOOTER_ZONES

def _clean(value) -> str:
    value = _ZERO_WIDTH_RE.sub(" ", str(value or ""))
    return re.sub(r"\s+", " ", value).strip()

def _compact(value) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

def _lines_from(text) -> list[str]:
    return [_clean(ln) for ln in str(text or "").splitlines() if _clean(ln)]

def _is_heading_style(style: str) -> bool:
    return bool(re.search(r"\b(heading|title)\b", style or "", re.IGNORECASE))

class TemplateAnalyzer:

    OPTIONAL_MARKER_PATTERN = _OPTIONAL_RE
    CONTACT_PATTERN = _CONTACT_RE
    IMAGE_PATTERN = _IMAGE_RE
    SUMMARY_PATTERN = _SUMMARY_RE

    @staticmethod
    def analyze_file(file_path: str, version: str) -> dict:
        parsed_data = TemplateAnalyzer._parse_template(file_path)
        return TemplateAnalyzer.analyze_parsed_data(parsed_data, version)

    @staticmethod
    def analyze_parsed_data(parsed_data: dict, version: str) -> dict:
        text = parsed_data.get("text", "")
        lines = [_clean(ln) for ln in text.splitlines() if _clean(ln)]

        components = TemplateAnalyzer._extract_components(lines, parsed_data)
        page_constraints = TemplateAnalyzer._extract_page_constraints(parsed_data)

        return TemplateSchemaGenerator.generate(
            version=version,
            components=components,
            page_constraints=page_constraints,
        )

    @staticmethod
    def _parse_template(file_path: str) -> dict:
        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".pdf":
            parsed_data = DocumentParser.parse_pdf(file_path)
            parsed_data["tables"] = TemplateAnalyzer._extract_pdf_tables(file_path)
            return parsed_data

        if extension == ".docx":
            parsed_data = DocumentParser.parse_docx(file_path)

            if not parsed_data.get("tables"):
                parsed_data["tables"] = TemplateAnalyzer._extract_docx_tables(file_path)
            return parsed_data

        raise ValueError(f"Unsupported template file type: {extension!r}")

    @staticmethod
    def _extract_components(lines: list[str], parsed_data: dict) -> dict:
        components = canonical_component_skeleton()
        tables = parsed_data.get("tables", [])
        layout = parsed_data.get("layout", [])
        paragraphs = parsed_data.get("paragraphs", [])

        components["header"] = TemplateAnalyzer._extract_header_component(
            lines, parsed_data
        )
        components["report_title"] = TemplateAnalyzer._extract_title_component(
            lines, parsed_data, paragraphs
        )
        components["event_information_table"] = (
            TemplateAnalyzer._extract_event_information_table(tables)
        )
        components["summary"] = TemplateAnalyzer._extract_summary_component(
            paragraphs,
            tables,
            parsed_data,
        )
        components["images"] = TemplateAnalyzer._extract_images_component(
            lines, parsed_data
        )
        components["signatures"] = TemplateAnalyzer._extract_signatures_component(
            lines, parsed_data
        )

        return components

    @staticmethod
    def _extract_header_component(lines, parsed_data):

        header_lines = TemplateAnalyzer._header_lines(
            lines,
            parsed_data,
        )

        elements = {}

        header_images = TemplateAnalyzer._header_images(
            parsed_data.get("layout", []),
            parsed_data.get("images", []),
        )

        if header_images["left"]:
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

        if header_images["right"]:
            elements["right_logo"] = {
                "required": False,
                "position": "top_right",
            }

        return {
            "required": True,
            "elements": elements,
        }

    @staticmethod
    def _detect_institution_info(
        lines: list[str], parsed_data: dict, file_type: str
    ) -> list[str]:
        if file_type == "docx":
            header_obj = parsed_data.get("header", {})
            h_lines = header_obj.get("lines", [])
            if h_lines:
                return h_lines

        title_line = TemplateAnalyzer._find_title_line(
            lines,
            parsed_data.get("paragraphs", []),
        )
        layout_lines: list[str] = []
        for page in parsed_data.get("layout", []):
            for block in page.get("text_blocks", []):
                zone = block.get("zone", "")
                if zone not in _HEADER_ZONES:
                    continue
                for ln in _lines_from(block.get("text", "")):
                    if ln == title_line:
                        continue
                    if _IMAGE_RE.search(ln):
                        continue
                    if ln not in layout_lines:
                        layout_lines.append(ln)
        if layout_lines:
            return layout_lines

        header_lines: list[str] = []
        for ln in lines:
            if ln == title_line:
                break
            if _IMAGE_RE.search(ln):
                continue
            if ln not in header_lines:
                header_lines.append(ln)
        return header_lines

    @staticmethod
    def _extract_title_component(
        lines: list[str], parsed_data: dict, paragraphs: list[dict]
    ) -> dict:
        title_line = TemplateAnalyzer._find_title_line(lines, paragraphs)
        component: dict = {
            "required": True,
            "position": "center",
            "label": "Report Title",
        }

        if title_line:
            component["label"] = title_line
            location = TemplateAnalyzer._find_text_location(
                title_line, parsed_data.get("layout", [])
            )
            if location:
                component["detected_position"] = (
                    TemplateAnalyzer._position_from_location(location)
                )

        return component

    @staticmethod
    def _find_title_line(
        lines: list[str], paragraphs: Optional[list[dict]] = None
    ) -> Optional[str]:

        for ln in lines:
            if _REPORT_TITLE_RE.search(ln):
                return ln

        if not paragraphs:
            return None

        candidates = []

        for para in paragraphs:

            text = _clean(para.get("text", ""))

            if not text:
                continue

            if _CONTACT_RE.search(text):
                continue

            if len(text.split()) > 12:
                continue

            score = 0

            if para.get("alignment") == "center":
                score += 4

            if _is_heading_style(para.get("style", "")):
                score += 3

            if para.get("bold"):
                score += 2

            if para.get("order", 999) <= 5:
                score += 2

            lower = text.lower()

            if "psg institute" in lower:
                score -= 10

            if "coimbatore" in lower:
                score -= 10

            if "neelambur" in lower:
                score -= 10

            candidates.append((score, text))

        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]

        return None

    @staticmethod
    def _extract_event_information_table(tables: list[dict]) -> dict:
        table = TemplateAnalyzer._select_event_information_table(tables)
        fields: dict = {}
        field_order: list[str] = []
        optional_fields: list[str] = []

        if table:
            for row_idx, row in enumerate(table.get("rows", [])):
                row = [_clean(str(c)) for c in row]
                if not any(row):
                    continue
                if len(row) < 2:
                    continue

                label = TemplateAnalyzer._label_from_table_row(row)
                if not label:
                    continue

                required = not _OPTIONAL_RE.search(label)
                clean_label = TemplateAnalyzer._clean_field_label(label)
                if not clean_label:
                    continue

                key = TemplateSchemaGenerator.normalize_key(clean_label)
                if key in fields:
                    continue

                canonical_key = TemplateAnalyzer._canonical_field_key(key, clean_label)
                final_key = canonical_key or key

                field_order.append(final_key)
                fields[final_key] = {
                    "label": clean_label,
                    "labels": [clean_label],
                    "aliases": list(
                        _KNOWN_FIELD_ALIASES.get(final_key, set())
                    ),
                    "required": required,
                    "row_order": row_idx,
                    "expected_type": _FIELD_EXPECTED_TYPES.get(final_key, "string"),
                }

                if not required:
                    optional_fields.append(final_key)
        
        required_order = [k for k in field_order if k not in optional_fields]

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
    def _select_event_information_table(tables: list[dict]) -> Optional[dict]:
        best_table = None
        best_score = -1

        for table in tables:

            score = 0
            rows = table.get("rows", [])

            for row in rows:

                row = [_clean(str(c)) for c in row]

                if not any(row):
                    continue

                if len(row) < 2:
                    continue

                label = TemplateAnalyzer._label_from_table_row(row)

                if not label:
                    continue

                compact = _compact(label)

                for aliases in _KNOWN_FIELD_ALIASES.values():

                    for alias in aliases:

                        alias = _compact(alias)

                        if compact == alias:
                            score += 5

                        elif alias in compact:
                            score += 2

            score += min(len(rows), 15)

            if score > best_score:
                best_score = score
                best_table = table

        return best_table if best_score > 0 else None

    @staticmethod
    def _row_matches_known_field(row: list) -> bool:

        row = [_clean(str(c)) for c in row]

        if not any(row):
            return False

        if len(row) < 2:
            return False

        label = TemplateAnalyzer._label_from_table_row(row)

        if not label:
            return False

        compact_label = _compact(_OPTIONAL_RE.sub("", label))

        for aliases in _KNOWN_FIELD_ALIASES.values():

            for alias in aliases:

                alias = _compact(alias)

                if compact_label == alias:
                    return True

                if alias in compact_label:
                    return True

        return False

    @staticmethod
    def _canonical_field_key(key: str, label: str) -> Optional[str]:

        compact_key = _compact(key)
        compact_label = _compact(label)

        for canonical, aliases in _KNOWN_FIELD_ALIASES.items():

            if compact_key == _compact(canonical):
                return canonical

            for alias in aliases:

                alias = _compact(alias)

                if compact_key == alias:
                    return canonical

                if compact_label == alias:
                    return canonical

                if alias in compact_label:
                    return canonical

        return None

    @staticmethod
    def _extract_summary_component(
        paragraphs: list[dict],
        tables: list[dict],
        parsed_data: dict,
    ) -> dict:

        summary_lines = []

        table_end_order = -1

        if tables:
            table_end_order = max(
                (
                    table.get("paragraph_order", -1)
                    for table in tables
                ),
                default=-1,
            )

        collecting = table_end_order == -1

        content_image_count = sum(
            1
            for img in parsed_data.get("images", [])
            if not img.get("is_header")
        )

        for para in paragraphs:

            order = para.get("order", -1)

            if not collecting and order > table_end_order:
                collecting = True

            if not collecting:
                continue

            text = _clean(para.get("text", ""))

            if not text:
                continue

            zone = para.get("zone", "")
            lower = text.lower()

            if zone in ("bottom_left", "bottom_right"):
                break

            if _SIGNATURE_ROLE_RE.search(text):
                break

            if (
                "psg institute" in lower
                or "neelambur" in lower
                or "coimbatore" in lower
            ):
                continue

            if (
                para.get("alignment") == "center"
                and (
                    para.get("bold")
                    or _is_heading_style(para.get("style", ""))
                )
            ):
                continue

            if (
                content_image_count > 0
                and para.get("alignment") == "center"
                and len(text.split()) <= 12
            ):
                break

            summary_lines.append(text)

        summary = "\n".join(summary_lines).strip()

        return {
            "required": True,
            "allowed_formats": [
                "paragraph",
                "bullets",
                "numbered",
            ],
            "position": {
                "after": "event_information_table",
                "before": "images",
            },
            "content": summary,
        }
    
    @staticmethod
    def _extract_images_component(lines: list[str], parsed_data: dict) -> dict:
        images = parsed_data.get("images", [])

        content_images = [img for img in images if not img.get("is_header")]
        header_image_count = len(images) - len(content_images)

        image_lines = [ln for ln in lines if _IMAGE_RE.search(ln)]

        caption_required = any(
            re.search(r"\b(caption|figure)\b", ln, re.IGNORECASE)
            for ln in image_lines
        ) or any("caption" in ln.lower() for ln in lines)

        required = (
            caption_required
            or bool(image_lines)
            or len(content_images) > 0
        )

        min_images, max_images = TemplateAnalyzer._extract_image_bounds(
            image_lines, required
        )

        if content_images and min_images == 0:
            min_images = 1
        if content_images and (max_images is None or max_images < len(content_images)):
            max_images = max(2, len(content_images))

        return {
            "required": required,
            "min_images": min_images,
            "max_images": max_images,
            "caption_required": caption_required,
            "caption_position": DEFAULT_CAPTION_POSITION,
            "exclude_header_images": True,
            "header_image_count": header_image_count,
        }

    @staticmethod
    def _extract_image_bounds(
        image_lines: list[str], required: bool
    ) -> tuple:
        numbers = []
        for ln in image_lines:
            numbers.extend(int(m) for m in re.findall(r"\b\d+\b", ln))

        if numbers:
            return min(numbers), max(numbers)
        if required:
            return 1, 2
        return 0, None

    @staticmethod
    def _extract_signatures_component(lines: list[str], parsed_data: dict) -> dict:
        elements: dict = {}
        file_type = parsed_data.get("file_type", "pdf")

        signature_labels = TemplateAnalyzer._signature_labels_from_layout(
            parsed_data.get("layout", [])
        )

        if not signature_labels and file_type == "docx":
            footer_obj = parsed_data.get("footer", {})
            footer_text = footer_obj.get("text", "")
            signature_labels = TemplateAnalyzer._signature_labels_from_text(
                footer_text
            )

        if not signature_labels:
            signature_labels = TemplateAnalyzer._signature_labels_from_lines(lines)

        for idx, sig in enumerate(signature_labels):
            label = sig.get("label", "")
            if not label:
                continue

            lower = label.lower()

            key = None

            for alias, canonical in SIGNATURE_KEY_MAPPING.items():

                if alias in lower:
                    key = canonical
                    break

            if key is None:
                key = TemplateSchemaGenerator.normalize_key(label)

            if key in elements:
                elements[key]["aliases"] = list(
                    dict.fromkeys(
                        elements[key]["aliases"] +
                        TemplateAnalyzer._signature_aliases(label)
                    )
                )
                continue

            position = SIGNATURE_POSITIONS.get(
                key,
                sig.get("position")
            )

            elements[key] = {
                "label": label,
                "aliases": TemplateAnalyzer._signature_aliases(label),
                "required": True,
                "position": position,
                "detection_strategy": sig.get("detection_strategy", DEFAULT_DETECTION_STRATEGY),
            }

        return {"required": True, "elements": elements}

    @staticmethod
    def _signature_labels_from_layout(pages: list[dict]) -> list[dict]:
        labels: list[dict] = []

        for page in pages:
            pw = page.get("width") or 1
            ph = page.get("height") or 1

            for block in page.get("text_blocks", []):
                zone = block.get("zone", "")
                cx = block.get("x0", 0)
                cy_raw = block.get("y0", 0)

                cy_norm = cy_raw / ph
                if zone not in _FOOTER_ZONES and cy_norm < 0.75:
                    continue

                cx_norm = (
                    (block.get("x0", 0) + block.get("x1", pw)) / 2
                ) / pw
                position = "bottom_left" if cx_norm < 0.5 else "bottom_right"

                text = block.get("text", "")
                for candidate in TemplateAnalyzer._split_signature_text(text):
                    if not _SIGNATURE_ROLE_RE.search(candidate):
                        continue
                    labels.append({
                        "label": candidate,
                        "position": position,
                        "detection_strategy": "layout",
                    })

        if len(labels) == 1:
            parts = TemplateAnalyzer._split_signature_text(labels[0]["label"])
            if len(parts) > 1:
                return [
                    {
                        "label": part,
                        "position": "bottom_left" if i == 0 else "bottom_right",
                        "detection_strategy": "layout",
                    }
                    for i, part in enumerate(parts)
                ]

        return labels

    @staticmethod
    def _signature_labels_from_text(text: str) -> list[dict]:
        labels: list[dict] = []
        for i, candidate in enumerate(
            TemplateAnalyzer._split_signature_text(text)
        ):
            if _SIGNATURE_ROLE_RE.search(candidate):
                labels.append({
                    "label": candidate,
                    "position": "bottom_left" if i == 0 else "bottom_right",
                    "detection_strategy": "footer_text",
                })
        return labels

    @staticmethod
    def _signature_labels_from_lines(lines: list[str]) -> list[dict]:
        if not lines:
            return []
        tail = "\n".join(lines[-6:])
        return [
            {
                "label": label,
                "position": "bottom_left" if i == 0 else "bottom_right",
                "detection_strategy": "tail_lines",
            }
            for i, label in enumerate(
                TemplateAnalyzer._split_signature_text(tail)
            )
            if _SIGNATURE_ROLE_RE.search(label)
        ]

    @staticmethod
    def _split_signature_text(text: str) -> list[str]:
        cleaned = _ZERO_WIDTH_RE.sub(" ", str(text or ""))

        parts = re.split(
            r"\n|\t|\s{3,}",
            cleaned,
        )

        candidates: list[str] = []

        for part in parts:
            part = re.sub(
                r"(Club Coordinator)\s+(Principal)",
                r"\1\n\2",
                part,
                flags=re.IGNORECASE,
            )

            for line in part.split("\n"):

                line = _clean(line)

                if not line:
                    continue

                if len(line.split()) > 6:
                    continue

                if _IMAGE_RE.search(line):
                    continue

                if _SUMMARY_RE.search(line):
                    continue

                candidates.append(line)

        return list(dict.fromkeys(candidates))
    
    @staticmethod
    def _signature_aliases(label: str):

        from app.models.template_metadata import SIGNATURE_ALIASES

        lower = label.lower()

        for aliases in SIGNATURE_ALIASES.values():

            if any(alias.lower() in lower for alias in aliases):
                return aliases

        return [label]

    @staticmethod
    def _extract_page_constraints(parsed_data: dict) -> dict:
        page_count = parsed_data.get("page_count")
        if page_count and page_count > 0:
            return {
                "max_pages": page_count,
                "mode": "exact",
                "pages": page_count,
            }
        return {
            "max_pages": 1,
            "mode": "exact",
            "pages": 1,
        }

    @staticmethod
    def _extract_pdf_tables(file_path: str) -> list[dict]:
        tables: list[dict] = []

        with pdfplumber.open(file_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                extracted_tables = page.extract_tables() or []

                for table_idx, rows in enumerate(extracted_tables):

                    normalized = [
                        [_clean(cell or "") for cell in row]
                        for row in rows
                    ]

                    tables.append(
                        {
                            "page_number": page_idx + 1,
                            "table_index": table_idx,
                            "rows": normalized,

                            "paragraph_order": table_idx,
                        }
                    )

        return tables

    @staticmethod
    def _extract_docx_tables(file_path: str) -> list[dict]:
        doc = Document(file_path)

        tables = []

        for table_idx, table in enumerate(doc.tables):
            rows = [
                [_clean(cell.text) for cell in row.cells]
                for row in table.rows
            ]
            tables.append(
                {
                    "table_index": table_idx,
                    "page_number": None,
                    "rows": rows,

                    "paragraph_order": table_idx,
                }
            )

        return tables

    @staticmethod
    def _find_text_location(
        value: str, pages: list[dict]
    ) -> Optional[dict]:
        if not value:
            return None
        search_value = re.sub(r"\s+", " ", value).strip().lower()

        for page in pages:
            pw = page.get("width") or 1
            ph = page.get("height") or 1
            for block in page.get("text_blocks", []):
                block_text = re.sub(
                    r"\s+", " ", block.get("text", "")
                ).strip().lower()
                if search_value not in block_text:
                    continue
                x0 = block.get("x0", 0)
                y0 = block.get("y0", 0)
                x1 = block.get("x1", x0)
                y1 = block.get("y1", y0)
                return {
                    "page_number": page.get("page_number"),
                    "page_width": pw,
                    "page_height": ph,
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                    "center_x": (x0 + x1) / 2,
                    "center_y": (y0 + y1) / 2,
                }
        return None

    @staticmethod
    def _position_from_location(location: dict) -> str:
        pw = location.get("page_width") or 1
        ph = location.get("page_height") or 1
        cx = location.get("center_x", 0) / pw
        cy = location.get("center_y", 0) / ph

        if cy < 0.25:
            if cx < 0.33:
                return "top_left"
            if cx > 0.67:
                return "top_right"
            return "top_center"
        if cy > 0.75:
            return "bottom_left" if cx < 0.5 else "bottom_right"
        return "center"

    @staticmethod
    def _label_from_table_row(row: list) -> Optional[str]:
        if not row:
            return None
        for cell in row:
            cleaned = _clean(cell)
            if cleaned:
                return cleaned
        return None

    @staticmethod
    def _clean_field_label(label: str) -> str:
        label = _OPTIONAL_RE.sub("", label)
        label = re.sub(r"\s+", " ", label).strip(" :-")
        return label

    @staticmethod
    def _header_lines(lines: list[str], parsed_data: dict) -> list[str]:
        return TemplateAnalyzer._detect_institution_info(
            lines, parsed_data, parsed_data.get("file_type", "pdf")
        )
    
    @staticmethod
    def _header_images(pages, doc_images):

        images = {
            "left": False,
            "right": False,
        }

        # ---------- PDF ----------
        for page in pages:

            page_width = page.get("width") or 1
            page_height = page.get("height") or 1

            for image in page.get("images", []):

                center_x = (
                    image.get("x0", 0)
                    + image.get("x1", 0)
                ) / 2

                center_y = (
                    image.get("y0", 0)
                    + image.get("y1", 0)
                ) / 2

                center_x /= page_width
                center_y /= page_height

                if center_y > 0.25:
                    continue

                if center_x < 0.33:
                    images["left"] = True

                elif center_x > 0.67:
                    images["right"] = True

        # ---------- DOCX fallback ----------
        for image in doc_images:

            if not image.get("is_header"):
                continue

            zone = image.get("zone")

            if zone == "top_left":
                images["left"] = True

            elif zone == "top_right":
                images["right"] = True

        return images

    @staticmethod
    def _clean_text(value) -> str:
        return _clean(value)

    @staticmethod
    def _lines_from_text(text) -> list[str]:
        return _lines_from(text)
