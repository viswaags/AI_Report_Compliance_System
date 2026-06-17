from pydantic import BaseModel


class ReviewActionRequest(BaseModel):
    report_id: int
    comments: str | None = None