import re

from app.models.canonical_report_model import CanonicalReportModel


class TemplateGuidedMapper:
    FIELD_ALIASES = {
        "coordinator": {
            "coordinator",
            "coordinators",
            "organizer",
            "organizers",
            "coordinatorsorganizers",
            "coordinatororganizer",
        },
        "coordinators_organizers": {
            "coordinator",
            "coordinators",
            "organizer",
            "organizers",
            "coordinatorsorganizers",
            "coordinatororganizer",
        },
        "number_of_participants": {
            "noofparticipants",
            "numberofparticipants",
            "participants",
            "participantcount",
        },
        "resource_person_event_in_charges": {
            "resourceperson",
            "resourcepersons",
            "eventincharge",
            "eventincharges",
            "resourcepersoneventincharges",
        },
    }

    @staticmethod
    def map(template_schema, raw_extraction):
        components = template_schema.get("components", {})
        model = CanonicalReportModel.empty()
        model["page_count"] = raw_extraction.get("page_count")

        model["header"] = TemplateGuidedMapper._map_header(
            components.get("header", {}),
            raw_extraction
        )
        model["event_information_table"] = TemplateGuidedMapper._map_event_table(
            components.get("event_information_table", {}),
            raw_extraction
        )
        model["report_title"] = TemplateGuidedMapper._map_report_title(
            components.get("report_title", {}),
            raw_extraction,
            model["header"],
            model["event_information_table"]
        )
        model["signatures"] = TemplateGuidedMapper._map_signatures(
            components.get("signatures", {}),
            raw_extraction
        )
        model["images"] = TemplateGuidedMapper._map_images(
            components.get("images", {}),
            raw_extraction
        )
        model["summary"] = TemplateGuidedMapper._map_summary(
            components.get("summary", {}),
            raw_extraction,
            model
        )
        model["detected_document_order"] = (
            TemplateGuidedMapper._detected_document_order(model)
        )

        return model

    @staticmethod
    def _map_header(header_schema, raw_extraction):
        elements = {}
        schema_elements = header_schema.get("elements", {})
        top_blocks = TemplateGuidedMapper._blocks_in_zones(
            raw_extraction,
            {"top_left", "top_center", "top_right"}
        )
        images = raw_extraction.get("images", [])

        for element, config in schema_elements.items():
            expected_position = config.get("position")
            element_data = {
                "present": False,
                "zone": None,
                "text": None,
            }

            if "logo" in element:
                image = TemplateGuidedMapper._first_image_in_zone(
                    images,
                    expected_position
                )
                if image:
                    element_data.update({
                        "present": True,
                        "zone": image.get("zone"),
                    })
            else:
                text = TemplateGuidedMapper._match_metadata_text(
                    config.get("metadata", []),
                    top_blocks
                )
                if not text and top_blocks:
                    text = "\n".join(block.get("text", "") for block in top_blocks)

                if text:
                    element_data.update({
                        "present": True,
                        "zone": expected_position,
                        "text": text,
                    })

            elements[element] = element_data

        return {
            "present": any(element.get("present") for element in elements.values()),
            "elements": elements,
        }

    @staticmethod
    def _map_report_title(title_schema, raw_extraction, header, table):
        label = title_schema.get("label")
        blocks = TemplateGuidedMapper._ordered_text_units(raw_extraction)
        header_text = TemplateGuidedMapper._joined_header_text(header)
        table_labels = set(table.get("field_sources", {}).values())
        table_texts = TemplateGuidedMapper._table_texts(table)
        expected_zone = title_schema.get("position")
        candidates = []

        for block in blocks:
            text = block.get("text", "")
            if not text or text in table_labels:
                continue

            if header_text and text in header_text:
                continue

            normalized_text = TemplateGuidedMapper._normalized(text)
            if (
                label
                and TemplateGuidedMapper._normalized(label) == normalized_text
                and TemplateGuidedMapper._is_generic_title_label(label)
            ):
                continue

            if normalized_text in table_texts:
                continue
            if TemplateGuidedMapper._starts_with_table_label(text, table):
                continue

            if TemplateGuidedMapper._looks_like_narrative_block(text):
                continue

            location = block.get("location") or {}
            if not TemplateGuidedMapper._is_centered(block):
                continue

            if not TemplateGuidedMapper._is_below_header(block, header):
                continue

            if block.get("zone") not in {expected_zone, "top_center", "center"}:
                continue

            candidates.append({
                "block": block,
                "score": TemplateGuidedMapper._title_score(block),
                "y": location.get("center_y", 0),
            })

        if candidates:
            candidates.sort(key=lambda item: (-item["score"], item["y"]))
            block = candidates[0]["block"]
            return {
                "present": True,
                "text": block.get("text"),
                "zone": block.get("zone"),
            }

        return {
            "present": False,
            "text": None,
            "zone": None,
        }

    @staticmethod
    def _map_event_table(table_schema, raw_extraction):
        field_configs = table_schema.get("fields", {})
        field_order = table_schema.get("field_order", [])
        table = TemplateGuidedMapper._select_matching_table(
            field_configs,
            raw_extraction.get("tables", [])
        )
        mapped_fields = {}
        mapped_order = []
        field_sources = {}

        if table:
            for row in table.get("rows", []):
                label = row.get("label")
                key = TemplateGuidedMapper._field_key_for_label(label, field_configs)
                if not key:
                    continue

                mapped_order.append(key)
                value = row.get("value")

                if not value:

                    cells = row.get("cells", [])

                    if len(cells) >= 2:
                        value = cells[-1]

                mapped_fields[key] = value
                field_sources[key] = label

        for key in field_order:
            mapped_fields.setdefault(key, None)

        return {
            "table_present": table is not None,
            "field_order": mapped_order,
            "expected_field_order": field_order,
            "fields": mapped_fields,
            "field_sources": field_sources,
            "unmapped_text": None if table else raw_extraction.get("text"),
        }

    @staticmethod
    def _map_summary(summary_schema, raw_extraction, model):
        text_units = TemplateGuidedMapper._ordered_text_units(raw_extraction)
        excluded = set()
        title_order = TemplateGuidedMapper._text_order_for(
            model["report_title"].get("text"),
            text_units
        )

        for element in model["header"].get("elements", {}).values():
            if element.get("text"):
                excluded.add(TemplateGuidedMapper._normalized(element["text"]))
                for line in element["text"].splitlines():
                    excluded.add(TemplateGuidedMapper._normalized(line))

        if model["report_title"].get("text"):
            excluded.add(TemplateGuidedMapper._normalized(model["report_title"]["text"]))

        for source in model["event_information_table"].get("field_sources", {}).values():
            excluded.add(TemplateGuidedMapper._normalized(source))

        for value in model["event_information_table"].get("fields", {}).values():
            if value:
                excluded.add(TemplateGuidedMapper._normalized(value))

        for caption in model.get("images", {}).get("captions", []):
            excluded.add(TemplateGuidedMapper._normalized(caption))

        summary_lines = []
        for unit in text_units:
            text = unit.get("text", "")
            normalized = TemplateGuidedMapper._normalized(text)
            if not text or normalized in excluded:
                continue
            if title_order is not None and (unit.get("order") or 0) <= title_order:
                continue
            if TemplateGuidedMapper._looks_like_caption(text):
                continue
            if TemplateGuidedMapper._looks_like_image_caption_text(text, model):
                continue
            if TemplateGuidedMapper._looks_like_signature_text(text, model):
                continue
            if TemplateGuidedMapper._looks_like_table_label(text, model):
                continue
            if TemplateGuidedMapper._looks_like_event_table_text(text, model):
                continue
            summary_lines.append(text)

        content = "\n".join(summary_lines).strip()
        return {
            "present": bool(content),
            "format": TemplateGuidedMapper._summary_format(content),
            "content": content or None,
            "allowed_formats": summary_schema.get("allowed_formats", []),
        }

    @staticmethod
    def _map_images(images_schema, raw_extraction):
        images = raw_extraction.get("images", [])
        captions = [
            image.get("caption")
            for image in images
            if image.get("caption")
        ]

        caption_count = len(captions)
        all_images_have_captions = (
            len(images) > 0
            and caption_count == len(images)
        )

        return {
            "count": len(images),
            "caption_present": all_images_have_captions,
            "captions": captions,
            "items": images,
        }

    @staticmethod
    def _map_signatures(signatures_schema, raw_extraction):
        mapped = {}
        blocks = TemplateGuidedMapper._ordered_text_units(raw_extraction)

        for element, config in signatures_schema.get("elements", {}).items():
            label = config.get("label") or element.replace("_", " ")
            match = TemplateGuidedMapper._find_signature_match(element, label, blocks)
            mapped[element] = {
            "present": match is not None,
            "label": label,
            "zone": match.get("zone") if match else None,
            "text": match.get("text") if match else None,
            "location": match.get("location") if match else None,
        }

        return mapped

    @staticmethod
    def _select_matching_table(field_configs, tables):
        best_table = None
        best_score = 0

        for table in tables:
            score = 0
            for row in table.get("rows", []):
                if TemplateGuidedMapper._field_key_for_label(
                    row.get("label"),
                    field_configs
                ):
                    score += 1

            if score > best_score:
                best_table = table
                best_score = score

        return best_table if best_score > 0 else None

    @staticmethod
    def _field_key_for_label(label, field_configs):
        normalized_label = TemplateGuidedMapper._compact_normalized(label)
        if not normalized_label:
            return None

        for key, config in field_configs.items():
            aliases = set(TemplateGuidedMapper.FIELD_ALIASES.get(key, set()))
            labels = [config.get("label"), *config.get("labels", [])]
            labels.extend(config.get("aliases", []))
            labels.append(key.replace("_", " "))
            for candidate in labels:
                normalized_candidate = TemplateGuidedMapper._compact_normalized(candidate)
                aliases.update(
                    TemplateGuidedMapper.FIELD_ALIASES.get(
                        normalized_candidate,
                        set()
                    )
                )
                if normalized_candidate:
                    aliases.add(normalized_candidate)

            if normalized_label in aliases:
                return key

            for candidate in aliases:
                if normalized_label == candidate:
                    return key

        return None

    @staticmethod
    def _detected_document_order(model):
        ordered = []
        if model.get("header", {}).get("present"):
            ordered.append("header")
        if model.get("report_title", {}).get("present"):
            ordered.append("report_title")
        if model.get("event_information_table", {}).get("table_present"):
            ordered.append("event_information_table")
        if model.get("summary", {}).get("present"):
            ordered.append("summary")
        non_header_images = [
            image
            for image in model.get("images", {}).get("items", [])
            if image.get("zone")
            not in {
                "top_left",
                "top_center",
                "top_right"
            }
        ]

        if non_header_images:
            ordered.append("images")
        if any(item.get("present") for item in model.get("signatures", {}).values()):
            ordered.append("signatures")
        return ordered

    @staticmethod
    def _ordered_text_units(raw_extraction):
        units = []
        units.extend(raw_extraction.get("text_blocks", []))
        units.extend(raw_extraction.get("paragraphs", []))
        return sorted(
            units,
            key=lambda item: (
                item.get("page_number") is None,
                item.get("page_number") or 0,
                item.get("order") or 0
            )
        )

    @staticmethod
    def _blocks_in_zones(raw_extraction, zones):
        return [
            block
            for block in TemplateGuidedMapper._ordered_text_units(raw_extraction)
            if block.get("zone") in zones
        ]

    @staticmethod
    def _first_image_in_zone(images, zone):
        for image in images:
            if image.get("zone") == zone:
                return image

        if zone is None and images:
            return images[0]

        return None

    @staticmethod
    def _match_metadata_text(metadata, blocks):
        metadata = [
            TemplateGuidedMapper._normalized(item)
            for item in metadata
            if item
        ]
        if not metadata:
            return None

        matched = []
        for block in blocks:
            normalized = TemplateGuidedMapper._normalized(block.get("text", ""))
            if any(item in normalized for item in metadata):
                matched.append(block.get("text", ""))

        return "\n".join(matched) if matched else None

    @staticmethod
    def _find_text_match(label, blocks):
        normalized_label = TemplateGuidedMapper._normalized(label)
        for block in blocks:
            if normalized_label in TemplateGuidedMapper._normalized(block.get("text", "")):
                return block
        return None

    @staticmethod
    def _find_signature_match(element, label, blocks):
        aliases = TemplateGuidedMapper._signature_aliases(element, label)

        for block in reversed(blocks):
            text = block.get("text", "")
            normalized_text = TemplateGuidedMapper._compact_normalized(text)
            for alias in aliases:
                if alias in normalized_text:
                    zone = block.get("zone")
                    if "principal" in alias:
                        zone = "bottom_right"
                    elif "coordinator" in alias:
                        zone = "bottom_left"
                    return {
                        **block,
                        "zone": zone,
                        "text": TemplateGuidedMapper._signature_display_text(
                            text,
                            alias,
                            label
                        ),
                    }

        return None

    @staticmethod
    def _summary_format(text):
        if re.search(r"(?m)^\s*\d+[.)]", text or ""):
            return "numbered"

        if re.search(r"(?m)^\s*(?:[-*]|[•●])", text or ""):
            return "bullets"

        return "paragraph" if text else None

    @staticmethod
    def _joined_header_text(header):
        return "\n".join(
            element.get("text", "")
            for element in header.get("elements", {}).values()
            if element.get("text")
        )

    @staticmethod
    def _looks_like_caption(text):
        return bool(re.search(r"\b(caption|fig(?:ure)?|image|photo)\b", text, re.IGNORECASE))

    @staticmethod
    def _looks_like_signature_text(text, model):
        normalized = TemplateGuidedMapper._normalized(text)
        for signature in model.get("signatures", {}).values():
            if TemplateGuidedMapper._normalized(signature.get("label")) in normalized:
                return True
        if re.search(
            r"\b(?:faculty|club)\s+co-?ordinator\b|\bprincipal\b",
            text or "",
            re.IGNORECASE
        ):
            return True
        return False

    @staticmethod
    def _looks_like_table_label(text, model):
        normalized = TemplateGuidedMapper._normalized(text)
        table = model.get("event_information_table", {})
        for source in table.get("field_sources", {}).values():
            if TemplateGuidedMapper._normalized(source) == normalized:
                return True
        return False

    @staticmethod
    def _looks_like_event_table_text(text, model):
        normalized = TemplateGuidedMapper._normalized(text)
        table = model.get("event_information_table", {})
        for source, value in zip(
            table.get("field_sources", {}).values(),
            table.get("fields", {}).values()
        ):
            source_normalized = TemplateGuidedMapper._normalized(source)
            value_normalized = TemplateGuidedMapper._normalized(value)
            if source_normalized and normalized.startswith(source_normalized):
                return True
            if value_normalized and value_normalized == normalized:
                return True
        for source in table.get("field_sources", {}).values():
            source_normalized = TemplateGuidedMapper._normalized(source)
            if source_normalized and normalized.startswith(source_normalized):
                return True
        for value in table.get("fields", {}).values():
            value_normalized = TemplateGuidedMapper._normalized(value)
            if value_normalized and (
                value_normalized == normalized or normalized in value_normalized
            ):
                return True
        return False

    @staticmethod
    def _looks_like_image_caption_text(text, model):
        normalized = TemplateGuidedMapper._normalized(text)
        for caption in model.get("images", {}).get("captions", []):
            caption_normalized = TemplateGuidedMapper._normalized(caption)
            if caption_normalized and (
                normalized in caption_normalized
                or caption_normalized in normalized
            ):
                return True
        return False

    @staticmethod
    def _starts_with_table_label(text, table):
        normalized = TemplateGuidedMapper._normalized(text)
        for source in table.get("field_sources", {}).values():
            source_normalized = TemplateGuidedMapper._normalized(source)
            if source_normalized and normalized.startswith(source_normalized):
                return True
        return False

    @staticmethod
    def _normalized(value):
        return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

    @staticmethod
    def _compact_normalized(value):
        return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

    @staticmethod
    def _table_texts(table):
        texts = set()
        fields = table.get("fields", {})
        sources = table.get("field_sources", {})
        for key, value in fields.items():
            source = sources.get(key)
            for item in (source, value, f"{source} {value}" if source and value else None):
                if item:
                    texts.add(TemplateGuidedMapper._normalized(item))
        return texts

    @staticmethod
    def _is_centered(block):
        location = block.get("location") or {}
        page_width = location.get("page_width") or 0
        center_x = location.get("center_x")
        if not page_width or center_x is None:
            return block.get("zone") in {"top_center", "center"}
        return abs((center_x / page_width) - 0.5) <= 0.18

    @staticmethod
    def _is_below_header(block, header):
        block_y = (block.get("location") or {}).get("center_y")
        if block_y is None:
            return True

        header_bottom = 120
        for element in header.get("elements", {}).values():
            text = element.get("text")
            if not text:
                continue
            for line in text.splitlines():
                if line and line in block.get("text", ""):
                    return False

        return block_y > header_bottom

    @staticmethod
    def _title_score(block):
        text = block.get("text", "")
        location = block.get("location") or {}
        width = max(location.get("x1", 0) - location.get("x0", 0), 0)
        height = max(location.get("y1", 0) - location.get("y0", 0), 0)
        uppercase_bonus = 50 if text.isupper() else 0
        report_bonus = 100 if "report" in text.lower() else 0
        return width + (height * 4) + uppercase_bonus + report_bonus

    @staticmethod
    def _looks_like_narrative_block(text):
        if re.search(r"[•●]", text or ""):
            return True
        word_count = len((text or "").split())

        return (
            word_count > 20
        )

    @staticmethod
    def _is_generic_title_label(label):
        return TemplateGuidedMapper._normalized(label) in {
            "report title",
            "title",
            "event report title",
        }

    @staticmethod
    def _text_order_for(text, text_units):
        normalized_text = TemplateGuidedMapper._normalized(text)
        if not normalized_text:
            return None
        for unit in text_units:
            if TemplateGuidedMapper._normalized(unit.get("text")) == normalized_text:
                return unit.get("order") or 0
        return None

    @staticmethod
    def _signature_aliases(element, label):
        aliases = {
            TemplateGuidedMapper._compact_normalized(label),
            TemplateGuidedMapper._compact_normalized(element.replace("_", " ")),
        }
        element_aliases = {
            "faculty_coordinator": ["faculty coordinator", "club coordinator"],
            "faculty_coordinator_club_coordinator": [
                "faculty coordinator",
                "club coordinator",
            ],
            "club_coordinator": ["club coordinator", "faculty coordinator"],
            "principal": ["principal"],
        }
        for part in re.split(r"/|,|\bor\b", label or "", flags=re.IGNORECASE):
            aliases.add(TemplateGuidedMapper._compact_normalized(part))
        for alias in element_aliases.get(element, []):
            aliases.add(TemplateGuidedMapper._compact_normalized(alias))
        return {alias for alias in aliases if alias}

    @staticmethod
    def _signature_display_text(text, matched_alias, fallback):
        signature_labels = [
            "Faculty Coordinator",
            "Club Coordinator",
            "Principal",
        ]
        for label in signature_labels:
            if TemplateGuidedMapper._compact_normalized(label) == matched_alias:
                return label
        return fallback
