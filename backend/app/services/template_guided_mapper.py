from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from app.models.canonical_report_model import CanonicalReportModel

_ROLE_PATTERN = re.compile(
    r"""
    \b(?:
        principal | director | dean | registrar | warden
        | hod | head\s+of\s+(?:department|dept)
        | faculty\s+(?:co-?ordinator|advisor|mentor|guide|incharge|in\s*charge)
        | club\s+(?:co-?ordinator|advisor|secretary|president)
        | event\s+(?:co-?ordinator|incharge|in\s*charge|manager)
        | staff\s+(?:advisor|co-?ordinator|incharge)
        | co-?ordinator | convenor | convener
        | joint\s+secretary | secretary | treasurer
        | president | vice[\s-]president
        | in[\s-]?charge | incharge
        | program(?:me)?\s+(?:co-?ordinator|chair|director)
        | department\s+co-?ordinator
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_BULLET_RE = re.compile(
    r"^\s*(?:[-*\u2022\u25cf\u25e6\u2013\u2014\u2023\u25aa\u25ab])\s+"
)
_NUMBERED_RE = re.compile(r"^\s*\d+[.)]\s+")

_FIELD_ALIASES: dict[str, set[str]] = {
    "coordinators_organizers": {
        "coordinator", "coordinators", "organizer", "organizers",
        "coordinatorsorganizers", "coordinatororganizer",
        "co ordinator", "coorganizer",
    },
    "number_of_participants": {
        "noofparticipants", "numberofparticipants", "participants",
        "participantcount", "noparticipants", "numberparticipants",
        "no of students", "noofstudents", "numberofstudents",
    },
    "resource_person_event_in_charges": {
        "resourceperson", "resourcepersons", "eventincharge",
        "eventincharges", "resourcepersoneventincharges",
        "eventinchargesperson", "guestspeaker", "speaker",
    },
    "date_duration": {
        "date", "duration", "dateduration", "dateofevent",
        "eventdate", "dateandtime", "datedurationtime",
    },
}

_HEADER_ZONES: frozenset[str] = frozenset({"top_left", "top_center", "top_right"})

_FOOTER_ZONES: frozenset[str] = frozenset({"bottom_left", "bottom_right"})

@dataclass
class LayoutIndex:

    units: list[dict] = field(default_factory=list)

    by_zone: dict[str, list[dict]] = field(default_factory=dict)

    by_page: dict[int, list[dict]] = field(default_factory=dict)

    norm_bbox: dict[int, dict] = field(default_factory=dict)

    compact: dict[int, str] = field(default_factory=dict)

    normed: dict[int, str] = field(default_factory=dict)

    file_type: str = "pdf"


def _build_layout_index(raw_extraction: dict) -> LayoutIndex:

    idx = LayoutIndex(
        file_type=raw_extraction.get(
            "file_type",
            "pdf",
        )
    )

    raw_units = []

    raw_units.extend(
        raw_extraction.get("text_blocks", [])
    )

    raw_units.extend(
        raw_extraction.get("paragraphs", [])
    )

    def sort_key(unit):

        location = unit.get("location")

        if location:

            return (
                location.get("page_number", 1),
                location.get("y0", 0),
                location.get("x0", 0),
                unit.get("order", 0),
            )

        return (
            unit.get("page_number", 1) or 1,
            unit.get("order", 0),
            0,
            0,
        )

    raw_units.sort(key=sort_key)

    total_units = max(len(raw_units), 1)

    for order, unit in enumerate(raw_units):

        uid = id(unit)

        location = unit.get("location")

        if location:

            pw = location.get("page_width") or 1
            ph = location.get("page_height") or 1

            nb = {
                "page": location.get("page_number") or 1,
                "x0": location.get("x0", 0) / pw,
                "y0": location.get("y0", 0) / ph,
                "x1": location.get("x1", pw) / pw,
                "y1": location.get("y1", ph) / ph,
                "cx": location.get("center_x", pw / 2) / pw,
                "cy": location.get("center_y", ph / 2) / ph,
                "w": (
                    max(
                        location.get("x1", pw)
                        - location.get("x0", 0),
                        1,
                    )
                    / pw
                ),
                "h": (
                    max(
                        location.get("y1", ph)
                        - location.get("y0", 0),
                        1,
                    )
                    / ph
                ),
                "raw_h": max(
                    location.get("y1", ph)
                    - location.get("y0", 0),
                    1,
                ),
            }

        else:
            rel_y = (order + 1) / (total_units + 1)

            nb = {
                "page": 1,
                "x0": 0.10,
                "y0": rel_y,
                "x1": 0.90,
                "y1": rel_y + 0.02,
                "cx": 0.50,
                "cy": rel_y + 0.01,
                "w": 0.80,
                "h": 0.02,
                "raw_h": 16,
            }

        idx.norm_bbox[uid] = nb

        text = (unit.get("text") or "").strip()

        idx.compact[uid] = _compact(text)

        idx.normed[uid] = _norm(text)

        zone = unit.get("zone")

        if zone:
            idx.by_zone.setdefault(
                zone,
                [],
            ).append(unit)

        idx.by_page.setdefault(
            nb["page"],
            [],
        ).append(unit)

        idx.units.append(unit)

    return idx

def _norm(value) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

def _compact(value) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

def _is_signature_text(text: str) -> bool:
    return bool(_ROLE_PATTERN.search(text or ""))

def _summary_format(text: str) -> Optional[str]:
    if not text:
        return None
    lines = text.splitlines()
    has_bullet = any(_BULLET_RE.match(ln) for ln in lines)
    has_numbered = any(_NUMBERED_RE.match(ln) for ln in lines)
    if has_bullet and has_numbered:
        return "mixed"
    if has_numbered:
        return "numbered"
    if has_bullet:
        return "bullets"
    return "paragraph"

class TemplateGuidedMapper:
    FIELD_ALIASES = _FIELD_ALIASES

    @staticmethod
    def map(template_schema: dict, raw_extraction: dict) -> dict:
        components = template_schema.get("components", {})
        model = CanonicalReportModel.empty()
        model["page_count"] = raw_extraction.get("page_count")

        layout = _build_layout_index(raw_extraction)

        model["header"] = TemplateGuidedMapper._map_header(
            components.get("header", {}), raw_extraction, layout
        )
        model["event_information_table"] = TemplateGuidedMapper._map_event_table(
            components.get("event_information_table", {}), raw_extraction
        )
        model["report_title"] = TemplateGuidedMapper._map_report_title(
            components.get("report_title", {}), layout,
            model["header"], model["event_information_table"]
        )
        model["signatures"] = TemplateGuidedMapper._map_signatures(
            components.get("signatures", {}), layout
        )
        model["images"] = TemplateGuidedMapper._map_images(
            components.get("images", {}), raw_extraction, layout
        )
        model["summary"] = TemplateGuidedMapper._map_summary(
            components.get("summary", {}), layout, model
        )
        model["detected_document_order"] = (
            TemplateGuidedMapper._detected_document_order(model, layout)
        )

        return model
    
    @staticmethod
    def _map_header(
        header_schema: dict,
        raw_extraction: dict,
        layout: LayoutIndex,
    ) -> dict:

        elements: dict = {}
        schema_elements = header_schema.get("elements", {})
        images = raw_extraction.get("images", [])

        header_units = [
            u
            for u in layout.units
            if layout.norm_bbox[id(u)]["cy"] <= 0.20
            or u.get("zone") in _HEADER_ZONES
        ]

        for element, config in schema_elements.items():

            expected_zone = config.get("position")

            el_data = {
                "present": False,
                "zone": None,
                "text": None,
                "location": None,
            }

            if "logo" in element:

                img = TemplateGuidedMapper._first_image_in_zone(
                    images,
                    expected_zone,
                )

                if img:

                    el_data.update(
                        {
                            "present": True,
                            "zone": img.get("zone"),
                            "location": img.get("location"),
                        }
                    )

            else:
                meta = config.get("metadata", [])

                text = TemplateGuidedMapper._match_metadata_text(
                    meta,
                    header_units,
                    layout,
                )

                if not text:

                    candidates = []

                    institution_keywords = {
                        "psg",
                        "institute",
                        "technology",
                        "college",
                        "university",
                        "department",
                        "engineering",
                        "science",
                        "research",
                        "autonomous",
                        "coimbatore",
                        "neelambur",
                        "school",
                        "education",
                        "polytechnic",
                        "academy",
                        "campus",
                        "institution",
                        "faculty",
                    }

                    reject_keywords = {
                        "report",
                        "workshop",
                        "seminar",
                        "hackathon",
                        "competition",
                        "training",
                        "plantation",
                        "tree",
                        "python",
                        "coding",
                        "participants",
                        "summary",
                        "club",
                        "event",
                        "meeting",
                        "drive",
                        "lecture",
                        "orientation",
                        "guest",
                        "industrial",
                        "visit",
                        "session",
                        "program",
                    }

                    for unit in header_units:

                        txt = (unit.get("text") or "").strip()

                        if not txt:
                            continue

                        lower = txt.lower()

                        nb = layout.norm_bbox[id(unit)]

                        score = 0

                        # ---------------------------------
                        # institution words
                        # ---------------------------------

                        for word in institution_keywords:

                            if word in lower:
                                score += 40

                        # ---------------------------------
                        # reject obvious report titles
                        # ---------------------------------

                        for word in reject_keywords:

                            if word in lower:
                                score -= 30

                        # ---------------------------------
                        # titles are usually short
                        # ---------------------------------

                        wc = len(txt.split())

                        if wc <= 2:
                            continue

                        if wc >= 12:
                            score += 10

                        if wc >= 5:
                            score += 15

                        if wc >= 10:
                            score += 10

                        # ---------------------------------
                        # prefer top area
                        # ---------------------------------

                        score += max(
                            0,
                            15 - nb["cy"] * 60
                        )

                        if (
                            "report" in lower
                            and wc <= 10
                        ):
                            score -= 100

                        if (
                            "workshop" in lower
                            and wc <= 10
                        ):
                            score -= 60

                        if score > 0:

                            candidates.append(
                                (
                                    score,
                                    unit,
                                )
                            )

                    if candidates:
                        candidates.sort(
                            key=lambda x: (
                                -x[0],
                                layout.norm_bbox[id(x[1])]["cy"],
                            )
                        )

                        selected = []

                        seen = set()

                        for score, unit in candidates:

                            txt = (unit.get("text") or "").strip()

                            if not txt:
                                continue

                            lower = txt.lower()

                            # -------------------------------------------------
                            # Stop before the report title
                            # -------------------------------------------------

                            if (
                                "report" in lower
                                or "workshop" in lower
                                or "seminar" in lower
                                or "webinar" in lower
                                or "competition" in lower
                                or "hackathon" in lower
                            ) and len(txt.split()) <= 10:
                                continue

                            if txt not in seen:
                                selected.append(txt)
                                seen.add(txt)

                        text = "\n".join(selected[:4])

                if text:
                    metadata = [
                        line.strip()
                        for line in text.splitlines()
                        if line.strip()
                    ]

                    location = None

                    for unit in header_units:

                        if (unit.get("text") or "").strip() in text:

                            location = unit.get("location")
                            break

                    el_data.update(
                        {
                            "present": True,
                            "zone": expected_zone,
                            "text": text,
                            "metadata": metadata,
                            "location": location,
                        }
                    )

            elements[element] = el_data

        return {
            "present": any(
                e.get("present")
                for e in elements.values()
            ),
            "elements": elements,
        }

    @staticmethod
    def _map_report_title(
        title_schema: dict,
        layout: LayoutIndex,
        header: dict,
        table: dict,
    ) -> dict:

        header_norms = TemplateGuidedMapper._header_norm_set(header)
        table_norms = TemplateGuidedMapper._table_norm_set(table)

        header_bottom = TemplateGuidedMapper._header_bottom_y(layout)
        table_top = TemplateGuidedMapper._table_top_y_norm(table, layout)

        heights = [
            layout.norm_bbox[id(u)]["raw_h"]
            for u in layout.units
            if layout.norm_bbox[id(u)]["raw_h"] > 0
        ]
        median_h = _median(heights) if heights else 10.0

        candidates: list[dict] = []

        for unit in layout.units:
            uid = id(unit)
            text = (unit.get("text") or "").strip()

            wc = len(text.split())

            if wc > 18:
                continue

    
            if not text:
                continue

            nb = layout.norm_bbox[uid]
            cn = layout.compact[uid]
            nr = layout.normed[uid]

            # Hard exclusions
            if nr in header_norms:
                continue
            if nr in table_norms:
                continue
            if _is_signature_text(text):
                continue
            if _BULLET_RE.match(text) or _NUMBERED_RE.match(text):
                continue
            if nb["cy"] > 0.85:
                continue  # footer region
            if TemplateGuidedMapper._starts_with_table_label_norm(nr, table):
                continue

            score = TemplateGuidedMapper._title_score(
                unit, nb, text, median_h, header_bottom, table_top
            )
            if score < 30:
                continue

            candidates.append({"unit": unit, "score": score, "cy": nb["cy"]})

        if not candidates:
            return {"present": False, "text": None, "zone": None, "location": None}

        candidates.sort(key=lambda c: (-c["score"], c["cy"]))
        
        # Reject only if the best candidate is extremely weak.

        if candidates[0]["score"] < 15:

            return {
                "present": False,
                "text": None,
                "zone": None,
                "location": None,
            }

        candidates.sort(
            key=lambda c: (
                -c["score"],
                abs(layout.norm_bbox[id(c["unit"])]["cy"] - 0.18),
            )
        )

        if len(candidates) >= 2:

            if candidates[0]["score"] - candidates[1]["score"] < 8:

                candidates.sort(
                    key=lambda c: (
                        "report" not in c["unit"].get("text", "").lower(),
                        -c["score"],
                    )
                )

        best = candidates[0]["unit"]

        zone = best.get("zone")

        if zone is None:

            nb = layout.norm_bbox[id(best)]

            if nb["cy"] < 0.22:
                zone = "top_center"

            elif nb["cy"] < 0.40:
                zone = "center"

        return {
            "present": True,
            "text": best.get("text"),
            "zone": zone,
            "location": best.get("location"),
        }

    @staticmethod
    def _title_score(
        unit: dict,
        nb: dict,
        text: str,
        median_h: float,
        header_bottom: float,
        table_top: Optional[float],
    ) -> float:

        if header_bottom is None:
            header_bottom = 0.15

        if table_top is None:
            table_top = 0.45

        words = text.split()
        wc = len(words)
        score: float = 0.0

        title_keywords = {
            "report",
            "workshop",
            "seminar",
            "webinar",
            "training",
            "competition",
            "hackathon",
            "bootcamp",
            "conference",
            "symposium",
            "orientation",
            "guest lecture",
            "industrial visit",
        }

        lower = text.lower()

        for word in title_keywords:

            if word in lower:
                score += 35

        height_ratio = nb["raw_h"] / max(median_h, 1)

        if height_ratio >= 1.8:
            score += 60
        elif height_ratio >= 1.3:
            score += 35
        elif height_ratio >= 1.0:
            score += 15

        cx_dev = abs(nb["cx"] - 0.5)

        if cx_dev <= 0.10:
            score += 10

        elif cx_dev <= 0.25:
            score += 8

        elif cx_dev <= 0.45:
            score += 5

        if nb["w"] >= 0.35:
            score += 15
        elif nb["w"] >= 0.20:
            score += 8

        # ---------------------------------------------------------
        # Prefer title between header and table,
        # but allow slight overlap with header.
        # ---------------------------------------------------------

        title_top = max(
            0.01,
            header_bottom - 0.18,
        )

        if table_top is not None:
            title_bottom = table_top + 0.18
        else:
            title_bottom = 0.65

        if title_top <= nb["cy"] <= title_bottom:

            mid = (title_top + title_bottom) / 2

            distance = abs(nb["cy"] - mid)

            score += max(
                0,
                8 - distance * 18,
            )

        zone = unit.get("zone")

        if zone in {
            "top_center",
            "center",
            "top_left",
            "top_right",
        }:
            score += 8

        if text.isupper():
            score += 25

        elif wc > 0:

            uc_ratio = sum(
                1
                for w in words
                if w and w[0].isupper()
            ) / wc

            if uc_ratio >= 0.7:
                score += 12

            elif uc_ratio >= 0.5:
                score += 6

        if unit.get("style"):

            style = unit["style"].lower()

            if "title" in style:
                score += 70

            elif "heading 1" in style:
                score += 55

            elif "heading" in style:
                score += 35

        if unit.get("bold"):
            score += 20

        if unit.get("alignment") == "center":
            score += 25

        # Typical report titles are short.

        if 2 <= wc <= 10:
            score += 28

        elif 11 <= wc <= 14:
            score += 14

        elif wc == 1:

            score += 4

        elif wc > 12:

            score -= 60

        sent_ends = len(re.findall(r"[.!?]", text))

        if sent_ends >= 3:
            score -= 25

        elif sent_ends == 2:
            score -= 10

        if "," in text and wc > 8:
            score -= 12

        if wc > 12 and (
            "." in text
            or ", " in text
        ):
            score -= 30

        table_labels = {
            "club",
            "club name",
            "event title",
            "event category",
            "venue",
            "date",
            "date duration",
            "number of participants",
            "participants",
            "coordinator",
            "coordinators",
            "organizer",
            "organizers",
            "resource person",
            "faculty coordinator",
            "principal",
        }

        compact_text = _compact(text)

        for label in table_labels:
            lbl = _compact(label)

            if compact_text == lbl:
                score -= 100

            elif compact_text.startswith(lbl):
                score -= 80

            elif lbl in compact_text and len(compact_text) < 40:
                score -= 50

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if len(lines) > 4:
            score -= 40

        if wc > 25:
            score -= 40

        letters = sum(
            c.isalpha()
            for c in text
        )

        digits = sum(
            c.isdigit()
            for c in text
        )

        if letters > 0 and digits == 0:

            score += 8

        if text == text.upper() and wc <= 8:

            score += 15

        elif text.istitle():

            score += 8

        if "." in text and wc > 8:

            score -= 40

        if "," in text and wc > 10:

            score -= 20

        verbs = {
            "organized",
            "conducted",
            "held",
            "attended",
            "participated",
            "included",
            "completed",
            "concluded",
            "started",
            "ended",
            "aimed",
            "guided",
        }

        for verb in verbs:

            if f" {verb} " in f" {lower} ":
                score -= 40

        return score

    @staticmethod
    def _map_event_table(table_schema: dict, raw_extraction: dict) -> dict:

        field_configs = table_schema.get("fields", {})
        field_order = table_schema.get("field_order", [])
        table = TemplateGuidedMapper._select_matching_table(
            field_configs, raw_extraction.get("tables", [])
        )

        mapped_fields: dict = {}
        mapped_order: list = []
        field_sources: dict = {}
        field_locations: dict = {}
        prev_key: Optional[str] = None

        if table:
            for row in table.get("rows", []):
                label = row.get("label")
                key = TemplateGuidedMapper._field_key_for_label(label, field_configs)

                if not key:
                    if prev_key:
                        extra = TemplateGuidedMapper._row_text(row)
                        if extra and mapped_fields.get(prev_key):
                            mapped_fields[prev_key] = (
                                mapped_fields[prev_key] + "\n" + extra
                            )
                    continue

                prev_key = key
                mapped_order.append(key)
                value = TemplateGuidedMapper._row_value(row)
                mapped_fields[key] = value
                field_sources[key] = label
                field_locations[key] = row.get("location")

        for key in field_order:
            mapped_fields.setdefault(key, None)

        return {
            "table_present": table is not None,
            "field_order": mapped_order,
            "expected_field_order": field_order,
            "fields": mapped_fields,
            "field_sources": field_sources,
            "location": (
                table["rows"][0].get("location")
                if table
                and table.get("rows")
                else None
            ),
            "page_number": (
                table.get("page_number")
                if table
                else None
            ),
            "unmapped_text": (
                None
                if table
                else raw_extraction.get("text")
            ),
        }

    @staticmethod
    def _map_signatures(
        signatures_schema: dict,
        layout: LayoutIndex,
    ) -> dict:

        mapped = {}

        candidates = TemplateGuidedMapper._signature_candidates(layout)
        signature_block = (
            TemplateGuidedMapper
            ._signature_block(layout)
        )

        used = set()

        for element, config in signatures_schema.get("elements", {}).items():

            label = config.get("label") or element.replace("_", " ")

            match = TemplateGuidedMapper._find_best_signature(
                element=element,
                label=label,
                expected_zone=config.get("position"),
                candidates=candidates,
                used=used,
                layout=layout,
                signature_block=signature_block,
            )

            if match:
                used.add(id(match))

            mapped[element] = {
                "present": match is not None,
                "label": label,
                "zone": (
                    match.get("zone")
                    if match
                    else config.get("position")
                ),
                "text": (
                    match.get("text")
                    if match
                    else None
                ),
                "location": (
                    match.get("location")
                    if match
                    else None
                ),
            }

        return mapped
    
    @staticmethod
    def _signature_candidates(
        layout: LayoutIndex,
    ) -> list[dict]:

        candidates = []

        for unit in layout.units:

            text = (
                unit.get("text") or ""
            ).strip()

            if not text:
                continue

            nb = layout.norm_bbox[id(unit)]

            if nb["cy"] < 0.65:
                continue

            split_units = (
                TemplateGuidedMapper
                ._split_signature_candidate(unit)
            )

            candidates.extend(split_units)

        return candidates
    
    @staticmethod
    def _signature_block(layout: LayoutIndex):

        top = None
        bottom = None

        for unit in layout.units:

            text = (unit.get("text") or "").lower()

            if not _is_signature_text(text):
                continue

            nb = layout.norm_bbox[id(unit)]

            if top is None or nb["cy"] < top:
                top = nb["cy"]

            if bottom is None or nb["cy"] > bottom:
                bottom = nb["cy"]

        if top is None:

            return {
                "top": 0.90,
                "bottom": 1.00,
            }

        return {
            "top": max(0.85, top - 0.05),
            "bottom": 1.00,
        }
    
    @staticmethod
    def _find_best_signature(
        element,
        label,
        expected_zone,
        candidates,
        used,
        layout,
        signature_block,
    ):

        aliases = TemplateGuidedMapper._signature_aliases(
            element,
            label,
        )

        best = None
        best_score = -1

        for unit in candidates:

            if id(unit) in used:
                continue

            # ---------------------------------------------------------
            # Get layout information first
            # ---------------------------------------------------------

            location = unit.get("location") or {}

            pw = location.get("page_width") or 1
            ph = location.get("page_height") or 1

            nb = {
                "cx": (
                    location.get("center_x", pw / 2)
                    / pw
                ),
                "cy": (
                    location.get("center_y", ph / 2)
                    / ph
                ),
            }

            if (
                signature_block["top"] is not None
                and nb["cy"] < signature_block["top"] - 0.05
            ):
                continue

            score = 0

            text = (
                unit.get("text", "")
                .strip()
            )

            compact = _compact(text)

            lower_text = text.lower()

            # ---------------------------------------------------------
            # Alias matching
            # ---------------------------------------------------------

            for alias in aliases:

                if compact == alias:
                    score += 100

                elif compact.startswith(alias):
                    score += 80

                elif alias in compact:
                    score += 60

            # ---------------------------------------------------------
            # Position preference
            # ---------------------------------------------------------

            cx = nb["cx"]

            if expected_zone == "bottom_left":

                if cx <= 0.55:
                    score += 30

                elif cx <= 0.65:
                    score += 15

            if expected_zone == "bottom_right":

                if cx >= 0.45:
                    score += 30

                elif cx >= 0.35:
                    score += 15

            # ---------------------------------------------------------
            # Strong role matching
            # ---------------------------------------------------------

            if "principal" in element.lower():

                if "principal" in lower_text:
                    score += 120
                else:
                    score -= 60

            if "faculty" in element.lower():

                if "faculty" in lower_text:
                    score += 120

            if "club" in element.lower():

                if "club" in lower_text:
                    score += 120

            if "coordinator" in element.lower():

                if "coordinator" in lower_text:
                    score += 80

            # ---------------------------------------------------------
            # Prefer lower page region
            # ---------------------------------------------------------

            if nb["cy"] >= 0.70:
                score += 15

            elif nb["cy"] >= 0.65:
                score += 8

            # ---------------------------------------------------------
            # Keep best
            # ---------------------------------------------------------

            if score > best_score:
                best_score = score
                best = unit

        if best_score < 20:
            return None

        return {
            **best,
            "zone": (
                best.get("zone")
                or expected_zone
            ),
            "text": (
                best.get("text") or ""
            ).strip(),
        }

    @staticmethod
    def _map_images(
        images_schema: dict, raw_extraction: dict, layout: LayoutIndex
    ) -> dict:

        images = raw_extraction.get("images", [])
        file_type = layout.file_type

        enriched: list[dict] = []
        non_header_count = 0

        for img in images:
            img_copy = dict(img)
            location = img_copy.get("location") or {}

            is_header_img = (
                TemplateGuidedMapper._image_in_header_strip(img_copy)
            )

            if (
                not is_header_img
                and img_copy.get("zone") in _HEADER_ZONES
            ):
                page_height = location.get("page_height") or 1

                if (location.get("center_y", 0) / page_height) <= 0.16:
                    is_header_img = True

            img_copy["is_header"] = is_header_img

            # Ignore captions for header logos

            if is_header_img:
                img_copy["caption"] = None

            if not is_header_img:
                non_header_count += 1
                if not img_copy.get("caption"):
                    img_copy["caption"] = (
                        TemplateGuidedMapper._pdf_caption(img_copy, layout)
                        if file_type == "pdf"
                        else TemplateGuidedMapper._docx_caption(img_copy, layout)
                    )

            enriched.append(img_copy)

        captions = []

        for img in enriched:

            if img.get("is_header"):
                continue

            cap = img.get("caption")

            if not cap:
                continue

            if cap not in captions:
                captions.append(cap)

        header_count = sum(
            1
            for img in enriched
            if img.get("is_header")
        )

        content_count = sum(
            1
            for img in enriched
            if not img.get("is_header")
        )

        return {
            "total_count": len(enriched),
            "header_count": header_count,
            "content_count": content_count,
            "caption_present": bool(captions),
            "captions": captions,
            "items": enriched,
        }

    @staticmethod
    def _image_in_header_strip(image: dict) -> bool:

        location = image.get("location")

        if not location:
            return False

        page_height = location.get("page_height") or 1
        page_width = location.get("page_width") or 1

        top = location.get("y0", 0) / page_height
        bottom = location.get("y1", 0) / page_height

        left = location.get("x0", 0) / page_width
        right = location.get("x1", 0) / page_width

        width = right - left
        height = bottom - top

        if bottom <= 0.16:
            return True

        if top <= 0.10 and width <= 0.25 and height <= 0.18:
            return True

        return False
    
    @staticmethod
    def _find_caption(
        image: dict,
        layout: LayoutIndex,
    ) -> Optional[str]:

        location = image.get("location")
        if not location:
            return None

        image_page = location.get("page_number", 1)

        image_x0 = location.get("x0", 0)
        image_x1 = location.get("x1", 0)
        image_y1 = location.get("y1", 0)

        image_width = max(image_x1 - image_x0, 1)
        image_height = max(location.get("y1", 0) - location.get("y0", 0), 1)

        max_vertical_gap = image_height * 0.80
        min_overlap = image_width * 0.15

        nearby = []

        for unit in layout.by_page.get(image_page, []):

            text = (unit.get("text") or "").strip()

            if not text:
                continue

            if _is_signature_text(text):
                continue

            if len(text.split()) > 60:
                continue

            if _BULLET_RE.match(text):
                continue

            if _NUMBERED_RE.match(text):
                continue

            unit_loc = unit.get("location") or {}

            uy0 = unit_loc.get("y0", 0)

            if uy0 <= image_y1:
                continue

            if uy0 - image_y1 > max_vertical_gap:
                continue

            overlap = (
                min(image_x1, unit_loc.get("x1", 0))
                - max(image_x0, unit_loc.get("x0", 0))
            )

            if overlap < min_overlap:
                continue

            nearby.append(
                (
                    uy0,
                    text,
                )
            )

        if not nearby:
            return None

        nearby.sort(key=lambda x: x[0])

        caption_lines = []

        previous_y = None

        for y, text in nearby:

            if previous_y is not None:

                if (y - previous_y) > image_height * 0.40:
                    break

            caption_lines.append(text)

            previous_y = y

        caption = " ".join(caption_lines).strip()

        return caption or None
    
    @staticmethod
    def _pdf_caption(
        image: dict,
        layout: LayoutIndex,
    ) -> Optional[str]:

        return TemplateGuidedMapper._find_caption(
            image,
            layout,
        )
    
    @staticmethod
    def _docx_caption(
        image: dict,
        layout: LayoutIndex,
    ) -> Optional[str]:

        image_index = image.get("image_index", 0)

        paragraphs = [
            u
            for u in layout.units
            if u.get("order") is not None
        ]

        paragraphs.sort(
            key=lambda u: u.get("order", 0)
        )

        possible = []

        for unit in paragraphs:

            text = (unit.get("text") or "").strip()

            if not text:
                continue

            if _is_signature_text(text):
                continue

            wc = len(text.split())

            if wc < 2 or wc > 20:
                continue

            lower = text.lower()

            if "report" in lower:
                continue

            if lower.startswith("the "):
                continue

            if lower.startswith("this "):
                continue

            if lower.startswith("around "):
                continue

            if lower.startswith("a total"):
                continue

            if "." in text:
                continue

            possible.append(unit)

        if not possible:
            return None

        # One caption can describe multiple images.
        # Return the nearest unused short paragraph.

        return possible[0]["text"]

    '''
    @staticmethod
    def _pdf_caption(image: dict, layout: LayoutIndex) -> Optional[str]:
   
        loc = image.get("location")
        if not loc:
            return None

        ph = loc.get("page_height") or 1
        pw = loc.get("page_width") or 1
        img_page = loc.get("page_number")
        img_x0 = loc.get("x0", 0)
        img_x1 = loc.get("x1", 0)
        img_y1 = loc.get("y1", 0)
        img_h = max(loc.get("y1", 0) - loc.get("y0", 0), 1)
        img_w = max(img_x1 - img_x0, 1)

        max_gap = img_h * 0.60
        min_overlap = img_w * 0.10

        page_units = layout.by_page.get(img_page, [])
        candidates: list[tuple[float, str]] = []

        for unit in page_units:
            uloc = unit.get("location") or {}
            uy0 = uloc.get("y0", 0)
            ux0 = uloc.get("x0", 0)
            ux1 = uloc.get("x1", 0)

            if uy0 <= img_y1:
                continue
            if (uy0 - img_y1) > max_gap:
                continue

            overlap = min(img_x1, ux1) - max(img_x0, ux0)
            if overlap < min_overlap:
                continue

            text = (unit.get("text") or "").strip()
            if not text:
                continue
            if _is_signature_text(text):
                continue
            if len(text.split()) > 80:
                continue

            candidates.append((uy0, text))

        if not candidates:
            return None

        candidates.sort(key=lambda c: c[0])

        merge_gap = img_h * 0.30
        parts: list[str] = []
        prev_y: Optional[float] = None

        for uy0, text in candidates:
            if prev_y is not None and (uy0 - prev_y) > merge_gap:
                break
            parts.append(text)
            prev_y = uy0

        return " ".join(parts).strip() or None

    @staticmethod
    def _docx_caption(image: dict, layout: LayoutIndex) -> Optional[str]:
  
        img_idx = image.get("image_index", -1)

        for unit in layout.units:
            uord = unit.get("order", -1)
            if uord <= img_idx:
                continue

            text = (unit.get("text") or "").strip()
            if not text:
                continue
            if _is_signature_text(text):
                continue
            wc = len(text.split())
            if wc <= 50:
                return text
            break   

        return None
        '''

    @staticmethod
    def _map_summary(
        summary_schema: dict,
        layout: LayoutIndex,
        model: dict,
    ) -> dict:

        table = model["event_information_table"]
        header = model["header"]
        images_model = model.get("images", {})

        excl: set[str] = set()

        TemplateGuidedMapper._add_header_exclusions(excl, header)
        TemplateGuidedMapper._add_table_exclusions(excl, table)
        TemplateGuidedMapper._add_caption_exclusions(
            excl,
            images_model.get("captions", []),
        )

        title_text = model.get("report_title", {}).get("text")
        if title_text:
            excl.add(_norm(title_text))

        header_bot = TemplateGuidedMapper._header_bottom_y(layout)

        table_top, table_bot = (
            TemplateGuidedMapper._table_y_range(
                table,
                layout,
            )
        )

        sig_top = (
            TemplateGuidedMapper
            ._signature_block(layout)["top"]
        )

        raw_lines = []
        summary_location = None

        for unit in layout.units:

            uid = id(unit)

            text = (unit.get("text") or "").strip()

            if not text:
                continue

            text = (
                text
                .replace("ΓùÅΓÇï", "• ")
                .replace("ΓùÅ", "• ")
                .replace("ΓÇï", "")
            )

            nb = layout.norm_bbox[uid]
            cy = nb["cy"]

            nr = layout.normed[uid]

            if len(text) <= 2:
                continue

            if (
                cy <= header_bot
                and not (
                    _BULLET_RE.match(text)
                    or _NUMBERED_RE.match(text)
                )
            ):
                continue

            if (
                table_top is not None
                and table_bot is not None
                and table_top <= cy <= table_bot
            ):
                continue

            if (
                sig_top is not None
                and cy >= sig_top
            ):
                continue

            if nr in excl:
                continue

            if _is_signature_text(text):
                continue

            if TemplateGuidedMapper._starts_with_table_label_norm(
                nr,
                table,
            ):
                continue

            if TemplateGuidedMapper._is_pure_table_value(
                nr,
                table,
            ):
                continue

            if TemplateGuidedMapper._is_caption_text(
                nr,
                images_model.get("captions", []),
            ):
                continue

            if summary_location is None:
                summary_location = unit.get("location")

            raw_lines.append(text)

        if layout.file_type == "pdf":

            expanded = []

            for line in raw_lines:

                line = line.replace("ΓùÅ", "\n• ")

                for piece in line.split("\n"):

                    piece = piece.strip()

                    if piece:
                        expanded.append(piece)

            lines = TemplateGuidedMapper._merge_wrapped_lines(
                expanded
            )

        else:

            lines = TemplateGuidedMapper._merge_wrapped_lines(
                raw_lines
            )

        content = "\n".join(lines).strip()

        return {
            "present": bool(content),
            "format": (
                _summary_format(content)
                if content
                else None
            ),
            "content": content or None,
            "allowed_formats": summary_schema.get(
                "allowed_formats",
                [],
            ),
            "after": "event_information_table",
            "before": (
                "images"
                if model.get("images", {}).get(
                    "content_count",
                    model.get("images", {}).get(
                        "non_header_count",
                        0,
                    ),
                ) > 0
                else "signatures"
            ),
            "location": summary_location,
        }
        

    @staticmethod
    def _detected_document_order(
        model: dict,
        layout: LayoutIndex,
    ) -> list[str]:

        components = []

        def add(component_name, location):
            if not location:
                return

            components.append(
                (
                    location.get("page_number", 1),
                    location.get("center_y", 0),
                    component_name,
                )
            )

        header = model.get("header", {})

        for element in header.get("elements", {}).values():

            location = element.get("location")

            if location:
                add("header", location)
                break

        title = model.get("report_title", {})

        add(
            "report_title",
            title.get("location"),
        )

        table = model.get("event_information_table", {})

        table_locations = [
            loc
            for loc in table.get("field_locations", {}).values()
            if loc
        ]

        if table_locations:

            add(
                "event_information_table",
                min(
                    table_locations,
                    key=lambda loc: (
                        loc.get("page_number", 1),
                        loc.get("center_y", 0),
                    ),
                ),
            )

        summary = model.get("summary", {})

        if summary.get("location"):

            add(
                "summary",
                summary["location"],
            )

        images = model.get("images", {}).get("items", [])

        image_locations = [
            image["location"]
            for image in images
            if (
                image.get("location")
                and not image.get("is_header")
            )
        ]

        if image_locations:

            add(
                "images",
                min(
                    image_locations,
                    key=lambda loc: (
                        loc.get("page_number", 1),
                        loc.get("center_y", 0),
                    ),
                ),
            )

        signatures = model.get("signatures", {})

        signature_locations = [
            sig.get("location")
            for sig in signatures.values()
            if sig.get("location")
        ]

        if signature_locations:

            add(
                "signatures",
                min(
                    signature_locations,
                    key=lambda loc: (
                        loc.get("page_number", 1),
                        loc.get("center_y", 0),
                    ),
                ),
            )

        components.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        ordered = []

        for _, _, component in components:

            if component not in ordered:
                ordered.append(component)

        return ordered

    @staticmethod
    def _header_bottom_y(layout: LayoutIndex) -> float:

        top_units = [
            u for u in layout.units
            if layout.norm_bbox[id(u)]["cy"] <= 0.28
            or u.get("zone") in _HEADER_ZONES
        ]
        if not top_units:
            return 0.15
        return max(layout.norm_bbox[id(u)]["y1"] for u in top_units)

    @staticmethod
    def _table_top_y_norm(table: dict, layout: LayoutIndex) -> Optional[float]:
        src_norms = {
            _norm(s)
            for s in table.get("field_sources", {}).values()
            if s
        }
        for unit in layout.units:
            if layout.normed[id(unit)] in src_norms:
                return layout.norm_bbox[id(unit)]["cy"]
        return None

    @staticmethod
    def _table_y_range(
        table: dict, layout: LayoutIndex
    ) -> tuple[Optional[float], Optional[float]]:

        table_norms: set[str] = set()
        for src in table.get("field_sources", {}).values():
            if src:
                table_norms.add(_norm(src))
        for val in table.get("fields", {}).values():
            if val:
                table_norms.add(_norm(val))

        matched_ys: list[float] = []
        for unit in layout.units:
            if layout.normed[id(unit)] in table_norms:
                nb = layout.norm_bbox[id(unit)]
                matched_ys.append(nb["cy"])

        if not matched_ys:
            return None, None
        return (
            min(matched_ys) - 0.01,
            max(matched_ys) + 0.01,
        )

    @staticmethod
    def _signature_top_y(
        signatures,
        layout,
    ):

        block = TemplateGuidedMapper._signature_block(
            layout
        )

        if block["top"] is not None:
            return block["top"]

        return 0.82

    @staticmethod
    def _add_header_exclusions(excl: set, header: dict) -> None:
        for el in header.get("elements", {}).values():
            raw = el.get("text") or ""
            excl.add(_norm(raw))
            for line in raw.splitlines():
                excl.add(_norm(line))

    @staticmethod
    def _add_table_exclusions(excl: set, table: dict) -> None:
        for src in table.get("field_sources", {}).values():
            excl.add(_norm(src))
        for val in table.get("fields", {}).values():
            if val:
                excl.add(_norm(val))

    @staticmethod
    def _add_caption_exclusions(excl: set, captions: list) -> None:
        for cap in captions:
            if cap:
                excl.add(_norm(cap))

    @staticmethod
    def _header_norm_set(header: dict) -> set[str]:
        norms: set[str] = set()
        for el in header.get("elements", {}).values():
            raw = el.get("text") or ""
            norms.add(_norm(raw))
            for line in raw.splitlines():
                norms.add(_norm(line))
        return norms

    @staticmethod
    def _table_norm_set(table: dict) -> set[str]:
        norms: set[str] = set()
        for src in table.get("field_sources", {}).values():
            norms.add(_norm(src))
        for val in table.get("fields", {}).values():
            if val:
                norms.add(_norm(val))
        return norms

    @staticmethod
    def _starts_with_table_label_norm(nr: str, table: dict) -> bool:
        for src in table.get("field_sources", {}).values():
            sn = _norm(src)
            if sn and nr.startswith(sn):
                return True
        return False

    @staticmethod
    def _is_pure_table_value(nr: str, table: dict) -> bool:
        for val in table.get("fields", {}).values():
            if val and _norm(val) == nr:
                return True
        return False

    @staticmethod
    def _is_caption_text(
        nr: str,
        captions: list,
    ) -> bool:

        if not nr:
            return False

        nr = _norm(nr)

        for cap in captions:

            cn = _norm(cap)

            if not cn:
                continue

            if nr == cn:
                return True

            if len(cn) > 15 and nr in cn:
                return True

            if len(nr) > 15 and cn in nr:
                return True

        return False

    @staticmethod
    def _signature_aliases(
        element: str,
        label: str,
    ) -> set[str]:

        aliases: set[str] = set()

        candidates = [
            element.replace("_", " "),
            label,
        ]

        for candidate in candidates:

            if not candidate:
                continue

            aliases.add(_compact(candidate))

            for part in re.split(
                r"/|,|\bor\b|\band\b",
                candidate,
                flags=re.IGNORECASE,
            ):

                part = part.strip()

                if not part:
                    continue

                aliases.add(_compact(part))

        extra = {
            "principal": {
                "principal",
                "headofinstitution",
            },

            "faculty_coordinator": {
                "facultycoordinator",
                "facultyadvisor",
                "facultymentor",
                "staffcoordinator",
            },

            "club_coordinator": {
                "clubcoordinator",
                "studentcoordinator",
                "coordinator",
            },

            "faculty_incharge": {
                "facultyincharge",
                "facultyinchargeofevent",
                "eventincharge",
                "incharge",
            },
        }

        aliases.update(
            extra.get(
                element,
                set(),
            )
        )

        aliases = {
            alias
            for alias in aliases
            if alias
            and alias not in {
                "faculty",
                "club",
                "student",
                "principal",
                "coordinator",
                "incharge",
            }
        }

        aliases.add(_compact(label))
        aliases.add(_compact(element.replace("_", " ")))

        return aliases
    
    @staticmethod
    def _split_signature_candidate(unit: dict) -> list[dict]:

        text = " ".join(
            (unit.get("text") or "").split()
        )

        lower = text.lower()

        roles = [

            ("faculty coordinator / club coordinator", "bottom_left"),

            ("faculty coordinator", "bottom_left"),

            ("club coordinator", "bottom_left"),

            ("faculty in-charge", "bottom_left"),

            ("faculty incharge", "bottom_left"),

            ("principal", "bottom_right"),

        ]

        found = []

        for role, zone in roles:

            pos = lower.find(role)

            if pos != -1:

                found.append(
                    (
                        pos,
                        role,
                        zone,
                    )
                )

        if len(found) <= 1:
            return [unit]

        found.sort()

        loc = dict(
            unit.get("location") or {}
        )

        page_width = loc.get(
            "page_width",
            1,
        )

        result = []

        for _, role, zone in found:

            piece_loc = dict(loc)

            if zone == "bottom_left":

                piece_loc["center_x"] = page_width * 0.20
                piece_loc["x0"] = page_width * 0.08
                piece_loc["x1"] = page_width * 0.32

            else:

                piece_loc["center_x"] = page_width * 0.80
                piece_loc["x0"] = page_width * 0.68
                piece_loc["x1"] = page_width * 0.92

            result.append(
                {
                    **unit,
                    "text": role.title(),
                    "zone": zone,
                    "location": piece_loc,
                }
            )

        return result
    '''
    @staticmethod
    def _split_signature_candidate(unit: dict) -> list[dict]:

        text = " ".join(
            (unit.get("text") or "").split()
        )

        lower = text.lower()

        roles = [

            "faculty coordinator / club coordinator",

            "faculty coordinator",

            "club coordinator",

            "faculty in-charge",

            "faculty incharge",

            "principal",

        ]

        matches = []

        for role in roles:

            start = lower.find(role)

            if start != -1:
                matches.append((start, role))

        if len(matches) <= 1:
            return [unit]

        matches.sort()

        result = []

        loc = unit.get("location") or {}

        page_width = loc.get("page_width", 1)

        x0 = loc.get("x0", 0)
        x1 = loc.get("x1", page_width)

        total_width = max(x1 - x0, 1)

        for index, (start, role) in enumerate(matches):

            end = (
                matches[index + 1][0]
                if index + 1 < len(matches)
                else len(text)
            )

            piece = text[start:end].strip()

            piece_loc = dict(loc)

            ratio0 = start / max(len(text), 1)
            ratio1 = end / max(len(text), 1)

            piece_loc["x0"] = x0 + ratio0 * total_width
            piece_loc["x1"] = x0 + ratio1 * total_width
            piece_loc["center_x"] = (
                piece_loc["x0"] +
                piece_loc["x1"]
            ) / 2

            result.append(
                {
                    **unit,
                    "text": piece,
                    "location": piece_loc,
                }
            )

        return result
    '''
    
    @staticmethod
    def _infer_sig_zone(
        element: str,
        label: str,
        bbox: dict,
    ):

        role = f"{element} {label}".lower()

        cx = bbox.get("cx")

        if cx is None:
            cx = (
                bbox.get("x0", 0)
                + bbox.get("x1", 0)
            ) / 2

        if "principal" in role:
            return "bottom_right"

        if (
            "faculty" in role
            or "club" in role
            or "coordinator" in role
        ):
            return "bottom_left"

        if cx <= 0.45:
            return "bottom_left"

        if cx >= 0.55:
            return "bottom_right"

        return "bottom_center"

    @staticmethod
    def _bottom_region_units(layout: LayoutIndex) -> list[dict]:

        result = []

        for unit in layout.units:

            nb = layout.norm_bbox[id(unit)]

            if (
                nb["cy"] >= 0.70
                or nb["y0"] >= 0.68
                or unit.get("zone") in _FOOTER_ZONES
            ):
                result.append(unit)

        result.sort(
            key=lambda u: (
                layout.norm_bbox[id(u)]["page"],
                layout.norm_bbox[id(u)]["cy"],
            )
        )

        return result

    @staticmethod
    def _merge_wrapped_lines(lines: list[str]) -> list[str]:

        paragraphs = []
        current = ""

        for raw_line in lines:

            line = raw_line.strip()

            if not line:

                if current:
                    paragraphs.append(current)

                current = ""
                continue

            # Start new paragraph for bullets/numbering
            if (
                _BULLET_RE.match(line)
                or _NUMBERED_RE.match(line)
            ):

                if current:
                    paragraphs.append(current)

                current = line
                continue

            # Very short headings should not merge
            if (
                len(line.split()) <= 3
                and line.isupper()
            ):

                if current:
                    paragraphs.append(current)

                current = line
                continue

            if current:

                if re.search(r"[.!?]\s*$", current):

                    paragraphs.append(current)
                    current = line

                else:

                    current += " " + line

            else:

                current = line

        if current:
            paragraphs.append(current)

        return [
            p.strip()
            for p in paragraphs
            if len(p.strip()) > 5
        ]

    @staticmethod
    def _select_matching_table(
        field_configs: dict, tables: list[dict]
    ) -> Optional[dict]:
        best_table: Optional[dict] = None
        best_score = 0

        for table in tables:
            score = sum(
                1
                for row in table.get("rows", [])
                if TemplateGuidedMapper._field_key_for_label(
                    row.get("label"), field_configs
                )
            )
            if score > best_score:
                best_table = table
                best_score = score

        return best_table if best_score > 0 else None

    @staticmethod
    def _field_key_for_label(
        label, field_configs: dict
    ) -> Optional[str]:
        nl = _compact(label)
        if not nl:
            return None

        for key, config in field_configs.items():
            aliases: set[str] = set(
                TemplateGuidedMapper.FIELD_ALIASES.get(key, set())
            )
            candidates = [
                config.get("label"),
                *config.get("labels", []),
                *config.get("aliases", []),
                key.replace("_", " "),
            ]
            for cand in candidates:
                cn = _compact(cand)
                aliases.update(
                    TemplateGuidedMapper.FIELD_ALIASES.get(cn, set())
                )
                if cn:
                    aliases.add(cn)

            if nl in aliases:
                return key

        return None

    @staticmethod
    def _row_value(row: dict) -> Optional[str]:
        value = row.get("value")
        if value:
            return value
        cells = row.get("cells", [])
        non_empty = [c for c in cells if c]
        return non_empty[-1] if len(non_empty) >= 2 else None

    @staticmethod
    def _row_text(row: dict) -> Optional[str]:
        cells = [c for c in row.get("cells", []) if c]
        return " ".join(cells).strip() or None

    @staticmethod
    def _first_image_in_zone(
        images: list[dict], zone: Optional[str]
    ) -> Optional[dict]:
        for img in images:
            if img.get("zone") == zone:
                return img
        if zone is None and images:
            return images[0]
        return None

    @staticmethod
    def _match_metadata_text(
        metadata,
        units,
        layout,
    ):

        meta_norms = [
            _norm(m)
            for m in metadata
            if m
        ]

        if not meta_norms:
            return None

        matched = []

        for unit in units:

            text = (
                unit.get("text") or ""
            ).strip()

            if not text:
                continue

            norm = layout.normed[id(unit)]

            score = 0

            for meta in meta_norms:

                if meta in norm:
                    score += 100

            if score:

                matched.append(
                    (
                        score,
                        text,
                    )
                )

        if not matched:
            return None

        matched.sort(
            reverse=True,
            key=lambda x: x[0]
        )

        return "\n".join(
            text
            for _, text in matched
        )

    @staticmethod
    def _joined_header_text(header: dict) -> str:
        return "\n".join(
            el.get("text", "")
            for el in header.get("elements", {}).values()
            if el.get("text")
        )

    @staticmethod
    def _ordered_text_units(raw_extraction: dict) -> list[dict]:
        return _build_layout_index(raw_extraction).units

def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0
