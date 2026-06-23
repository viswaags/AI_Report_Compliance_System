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
from fastapi import HTTPException, status
from app.auth.dependencies import get_current_user, require_role
from app.services.access_control_service import AccessControlService
from app.schemas.event import EventCreateFrontend
from app.auth.dependencies import (
    get_current_user
)

from app.models.event_record import (
    EventRecord
)

from sqlalchemy import distinct

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


@router.post("/")
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.STUDENT_REPRESENTATIVE,
            UserRole.CLUB_COORDINATOR,
            UserRole.ADMIN
        ])
    )
):

    if current_user.role != UserRole.ADMIN:

        if not AccessControlService.user_has_club_access(
            db,
            current_user.id,
            event.club_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this club"
            )

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
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR,
            UserRole.STUDENT_REPRESENTATIVE,
            UserRole.FACULTY_REPRESENTATIVE
        ])
    )
):

    if current_user.role == UserRole.ADMIN:

        return (
            db.query(Event)
            .all()
        )

    club_ids = (
        AccessControlService
        .get_accessible_club_ids(
            db,
            current_user.id
        )
    )

    return (
        db.query(Event)
        .filter(
            Event.club_id.in_(club_ids)
        )
        .all()
    )

@router.get("/categories")
def event_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    categories = (
        db.query(
            distinct(
                Event.event_category
            )
        )
        .all()
    )

    return [
        category[0]
        for category in categories
        if category[0]
    ]

@router.get("/my-events")
def my_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    club_ids = (
        AccessControlService
        .get_accessible_club_ids(
            db,
            current_user.id
        )
    )

    return (
        db.query(Event)
        .filter(
            Event.club_id.in_(club_ids)
        )
        .all()
    )

@router.get("/club/{club_id}")
def events_by_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        db.query(Event)
        .filter(
            Event.club_id == club_id
        )
        .all()
    )



@router.get("/{event_id}/stats")
def event_stats(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    event = (
        db.query(Event)
        .filter(
            Event.id == event_id
        )
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    record = (
        db.query(EventRecord)
        .filter(
            EventRecord.event_id == event_id
        )
        .first()
    )

    return {
        "event_id": event.id,
        "event_title": event.event_title,
        "event_category": event.event_category,
        "event_date": event.event_date,
        "approved": record is not None,
        "participant_count":
            record.participant_count
            if record else 0
    }

@router.get("/{event_id}")
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    event = (
        db.query(Event)
        .filter(
            Event.id == event_id
        )
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return event


'''
@router.post("/create-my-event")
def create_my_event(
    event: EventCreateFrontend,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.STUDENT_REPRESENTATIVE
        )
    )
):'''