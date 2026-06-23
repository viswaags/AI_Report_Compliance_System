from pydantic import BaseModel
from datetime import date

class EventCreate(BaseModel):

    club_id: int

    event_title: str

    event_category: str | None = None

    event_date: date | None = None

class EventCreateFrontend(BaseModel):

    event_title: str

    event_category: str | None = None

    event_date: date | None = None