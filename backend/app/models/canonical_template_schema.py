from copy import deepcopy


DOCUMENT_COMPONENT_ORDER = [
    "header",
    "report_title",
    "event_information_table",
    "summary",
    "images",
    "signatures",
]


ALLOWED_SUMMARY_FORMATS = [
    "paragraph",
    "bullets",
    "numbered",
]


ZONE_RANGES = {
    "top_left": {
        "x_range": [0, 0.33],
        "y_range": [0, 0.25],
    },
    "top_center": {
        "x_range": [0.33, 0.67],
        "y_range": [0, 0.25],
    },
    "top_right": {
        "x_range": [0.67, 1],
        "y_range": [0, 0.25],
    },
    "center": {
        "x_range": [0.25, 0.75],
        "y_range": [0.25, 0.75],
    },
    "bottom_left": {
        "x_range": [0, 0.5],
        "y_range": [0.75, 1],
    },
    "bottom_right": {
        "x_range": [0.5, 1],
        "y_range": [0.75, 1],
    },
}


def canonical_component_skeleton():
    return {
        "header": {
            "required": True,
            "elements": {},
        },
        "report_title": {
            "required": True,
            "position": "center",
        },
        "event_information_table": {
            "required": True,
            "table_required": True,
            "field_order": [],
            "fields": {},
            "optional_fields": [],
            "additional_fields": {
                "allowed": True,
                "must_appear_after": None,
            },
        },
        "summary": {
            "required": True,
            "allowed_formats": deepcopy(ALLOWED_SUMMARY_FORMATS),
        },
        "images": {
            "required": False,
            "min_images": 0,
            "max_images": None,
            "caption_required": False,
        },
        "signatures": {
            "required": True,
            "elements": {},
        },
    }
