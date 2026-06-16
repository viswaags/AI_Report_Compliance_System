from pydantic import BaseModel


class FeedbackGenerateResponse(
    BaseModel
):

    id: int

    feedback_text: str

    model_used: str

    class Config:
        from_attributes = True


class FeedbackBundleResponse(BaseModel):

    feedback: str

    feedback_id: int

    email_subject: str

    email_body: str
