from pydantic import BaseModel


class ReportCreate(BaseModel):

    event_id: int

    template_id: int