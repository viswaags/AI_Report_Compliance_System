from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.dependencies import get_db

from app.models.event import Event
from app.models.user import (
    User,
    UserRole
)

from app.schemas.event import EventCreate

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


@router.post("/")
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.STUDENT_REPRESENTATIVE
        )
    )
):
    db_event = Event(
        club_id=event.club_id,
        event_title=event.event_title,
        event_category=event.event_category,
        event_date=event.event_date
    )

    db.add(db_event)

    db.commit()

    db.refresh(db_event)

    return db_event


@router.get("/")
def get_events(
    db: Session = Depends(get_db)
):
    return db.query(
        Event
    ).all()