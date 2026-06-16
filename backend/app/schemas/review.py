from pydantic import BaseModel


class ReviewCreate(BaseModel):

    report_id: int

    reviewer_id: int

    status: str

    comments: str | None = None