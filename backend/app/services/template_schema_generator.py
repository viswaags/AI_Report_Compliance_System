from __future__ import annotations

import re
from copy import deepcopy

from app.models.canonical_template_schema import (
    DOCUMENT_COMPONENT_ORDER,
    ZONE_RANGES,
    canonical_component_skeleton,
)


class TemplateSchemaGenerator:

    @staticmethod
    def generate(
        version: str,
        components: dict,
        page_constraints: dict,
    ) -> dict:
        canonical_components = TemplateSchemaGenerator._canonical_components(components)
        field_configs = TemplateSchemaGenerator._event_table_field_configs(canonical_components)
        image_requirements = deepcopy(canonical_components.get("images", {}))

        page_limit = (
            page_constraints.get("max_pages")
            or page_constraints.get("exact_pages")
            or page_constraints.get("pages")
        )
        page_mode = page_constraints.get("mode", "max")

        schema = {
            "schema_type": "canonical_template_schema",
            "template_version": version,
            "page_constraints": {
                "max_pages": page_limit,
                "mode": page_mode,
                "pages": page_constraints.get("pages") or page_limit,
            },
            "components": canonical_components,
            "document_order": [
                component
                for component in DOCUMENT_COMPONENT_ORDER
                if component in canonical_components
            ],
            "layout_zones": deepcopy(ZONE_RANGES),
            "legacy_compatibility": {
                "fields_source": "components.event_information_table.fields",
                "images_source": "components.images",
                "page_constraints_source": "page_constraints",
            },
        }

        schema.update(
            TemplateSchemaGenerator._legacy_aliases(
                version=version,
                field_configs=field_configs,
                image_requirements=image_requirements,
                page_constraints=page_constraints,
                canonical_components=canonical_components,
            )
        )

        return schema

    @staticmethod
    def _canonical_components(components: dict) -> dict:
        canonical_components = canonical_component_skeleton()

        for component_name, component in components.items():
            if component_name not in canonical_components:
                continue
            if isinstance(component, dict):
                canonical_components[component_name].update(component)

        table = canonical_components["event_information_table"]
        table.setdefault("table_required", True)
        table.setdefault("field_order", [])
        table.setdefault("fields", {})
        table.setdefault("optional_fields", [])
        table.setdefault(
            "additional_fields",
            {"allowed": True, "must_appear_after": None},
        )

        for key, config in table.get("fields", {}).items():
            if isinstance(config, dict):
                config.setdefault("aliases", [])
                config.setdefault("expected_type", "string")

        for key, element in canonical_components.get("signatures", {}).get("elements", {}).items():
            if isinstance(element, dict):
                element.setdefault("aliases", [element.get("label", key)])
                element.setdefault("detection_strategy", "text")

        images = canonical_components.get("images", {})
        images.setdefault("caption_position", "below")
        images.setdefault("exclude_header_images", True)
        images.setdefault("header_image_count", 0)

        summary = canonical_components.get("summary", {})
        summary.setdefault("position", {
            "before": "images",
            "after": "event_information_table",
        })

        return canonical_components

    @staticmethod
    def _event_table_field_configs(components: dict) -> dict:
        table = components.get("event_information_table", {})
        fields = table.get("fields", {})
        field_configs: dict = {}

        if isinstance(fields, dict):
            for field, config in fields.items():
                if isinstance(config, dict):
                    field_configs[field] = deepcopy(config)
                else:
                    field_configs[field] = {
                        "required": True,
                        "label": field,
                        "aliases": [],
                        "expected_type": "string",
                    }

        return field_configs

    @staticmethod
    def _legacy_aliases(
        version,
        field_configs,
        image_requirements,
        page_constraints,
        canonical_components,
    ):
        required_sections = [
            component_name
            for component_name, component in canonical_components.items()
            if component.get("required", False)
        ]

        signature_elements = (
            canonical_components
            .get("signatures", {})
            .get("elements", {})
        )

        signature_section_map = {
            key: {
                "required": value.get("required", True),
                "position": value.get("position"),
            }
            for key, value in signature_elements.items()
        }

        signature_section_names = list(signature_section_map.keys())

        return {
            "version": version,

            "fields": field_configs,

            "layout_rules": {
                "zones": deepcopy(ZONE_RANGES),
                "page_limit": page_constraints,
                "latest_template_required": True,
            },

            "validation_rules": {
                "required_fields": [
                    field
                    for field, config in field_configs.items()
                    if config.get("required", True)
                ],
                "required_sections": required_sections,
                "section_order_required": False,
                "image_requirements": image_requirements,
                "signature_sections": signature_section_names,
            },

            "images": image_requirements,

            "signature_sections": signature_section_map,
        }

    @staticmethod
    def normalize_key(value: str) -> str:
        value = str(value or "")
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        return normalized or "unnamed"


# Claude Generated 2nd time.