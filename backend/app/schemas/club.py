from pydantic import BaseModel

class ClubCreate(BaseModel):
    club_name: str
    description: str | None = None


class ClubResponse(BaseModel):
    id: int
    club_name: str
    description: str | None = None

    class Config:
        from_attributes = True