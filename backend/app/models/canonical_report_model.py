from copy import deepcopy


CANONICAL_REPORT_COMPONENTS = [
    "header",
    "report_title",
    "event_information_table",
    "summary",
    "images",
    "signatures",
]


class CanonicalReportModel:

    @staticmethod
    def empty():
        return {
            "header": {
                "present": False,
                "elements": {},
            },
            "report_title": {
                "present": False,
                "text": None,
                "zone": None,
            },
            "event_information_table": {
                "table_present": False,
                "field_order": [],
                "fields": {},
                "field_sources": {},
                "unmapped_text": None,
            },
            "summary": {
                "present": False,
                "format": None,
                "content": None,
            },
            "images": {
                "count": 0,
                "caption_present": False,
                "captions": [],
                "items": [],
            },
            "signatures": {},
            "page_count": 0,
            "detected_document_order": [],
        }

    @staticmethod
    def from_parts(**parts):
        model = CanonicalReportModel.empty()

        for key, value in parts.items():
            if key in model:
                model[key] = deepcopy(value)

        return model
