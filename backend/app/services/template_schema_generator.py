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
        version,
        components,
        page_constraints
    ):
        canonical_components = TemplateSchemaGenerator._canonical_components(
            components
        )
        field_configs = TemplateSchemaGenerator._event_table_field_configs(
            canonical_components
        )
        image_requirements = deepcopy(
            canonical_components.get("images", {})
        )

        schema = {
            "schema_type": "canonical_template_schema",
            "template_version": version,
            "page_constraints": {
                "exact_pages": page_constraints.get("exact_pages")
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
                version,
                field_configs,
                image_requirements,
                page_constraints
            )
        )

        return schema

    @staticmethod
    def _canonical_components(components):
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
            {
                "allowed": True,
                "must_appear_after": None,
            }
        )

        return canonical_components

    @staticmethod
    def _event_table_field_configs(components):
        table = components.get("event_information_table", {})
        fields = table.get("fields", {})
        field_configs = {}

        if isinstance(fields, dict):
            for field, config in fields.items():
                field_configs[field] = (
                    deepcopy(config)
                    if isinstance(config, dict)
                    else {"required": True}
                )

        return field_configs

    @staticmethod
    def _legacy_aliases(
        version,
        field_configs,
        image_requirements,
        page_constraints
    ):
        return {
            "version": version,
            "fields": field_configs,
            "layout_rules": {
                "zones": deepcopy(ZONE_RANGES),
                "page_limit": page_constraints.get("exact_pages"),
                "latest_template_required": True,
            },
            "validation_rules": {
                "required_fields": [
                    field
                    for field, config in field_configs.items()
                    if config.get("required", True)
                ],
                "required_sections": [],
                "section_order_required": False,
                "image_requirements": image_requirements,
                "signature_sections": [],
            },
            "images": image_requirements,
            "signature_sections": {},
        }

    @staticmethod
    def normalize_key(value):
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        return normalized or "unnamed"
