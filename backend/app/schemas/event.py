from pydantic import BaseModel


class EventCreate(BaseModel):

    club_id: int

    event_title: str

    event_category: str | None = None

    event_date: str | None = None