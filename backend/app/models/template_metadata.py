from __future__ import annotations

import re

FIELD_ALIASES: dict[str, set[str]] = {
    "club": {"club"},
    "event_title": {"eventtitle", "title"},
    "event_category": {"eventcategory", "category"},
    "date_duration": {"date", "duration", "dateduration", "dateofevent", "eventdate"},
    "coordinators_organizers": {
        "coordinator", "coordinators", "organizer", "organizers",
        "coordinatorsorganizers", "coordinatororganizer",
    },
    "resource_person_event_in_charges": {
        "resourceperson", "eventincharge", "eventincharges",
        "resourcepersoneventincharges", "guestspeaker", "speaker",
    },
    "venue": {"venue", "location"},
    "number_of_participants": {
        "noofparticipants", "numberofparticipants", "participants",
        "participantcount", "noofstudents", "numberofstudents",
    },
}

FIELD_EXPECTED_TYPES: dict[str, str] = {
    "number_of_participants": "integer",
    "date_duration": "datetime",
    "budget": "currency",
    "event_title": "string",
    "club": "string",
    "venue": "string",
    "event_category": "string",
    "coordinators_organizers": "string",
    "resource_person_event_in_charges": "string",
}

SIGNATURE_ROLE_PATTERN: re.Pattern = re.compile(
    r"\b(?:principal|director|dean|hod|head\s+of\s+(?:department|dept)"
    r"|faculty\s+co-?ordinator|club\s+co-?ordinator|event\s+co-?ordinator"
    r"|staff\s+advisor|co-?ordinator|convenor|convener|secretary"
    r"|president|vice[\s-]president|in[\s-]?charge|incharge"
    r"|program(?:me)?\s+co-?ordinator)\b",
    re.IGNORECASE,
)

HEADER_ZONES: frozenset[str] = frozenset({"top_left", "top_center", "top_right"})

FOOTER_ZONES: frozenset[str] = frozenset({"bottom_left", "bottom_right"})

DEFAULT_DETECTION_STRATEGY: str = "text"

DEFAULT_CAPTION_POSITION: str = "below"

DEFAULT_SUMMARY_POSITION: dict[str, str] = {
    "before": "images",
    "after": "event_information_table",
}

SIGNATURE_ALIASES = {
    "faculty_coordinator_club_coordinator": [
        "faculty coordinator",
        "club coordinator",
        "faculty incharge",
        "faculty in-charge",
    ],
    "principal": [
        "principal",
    ],
}

SIGNATURE_KEY_MAPPING = {
    "faculty coordinator": "faculty_coordinator_club_coordinator",
    "club coordinator": "faculty_coordinator_club_coordinator",
    "faculty incharge": "faculty_coordinator_club_coordinator",
    "faculty in-charge": "faculty_coordinator_club_coordinator",
    "principal": "principal",
}

SIGNATURE_POSITIONS = {
    "faculty_coordinator_club_coordinator": "bottom_left",
    "principal": "bottom_right",
}
