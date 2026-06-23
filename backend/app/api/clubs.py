from fastapi import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.dependencies import get_db
from app.models.club import Club
from app.models.user import User, UserRole
from app.schemas.club import ClubCreate
from app.models.club_membership import (
    ClubMembership
)
from app.auth.dependencies import (
    get_current_user
)
from app.models.event import Event
from app.models.event_record import EventRecord

router = APIRouter(
    prefix="/clubs",
    tags=["Clubs"]
)


@router.get("/")
def get_clubs(
    db: Session = Depends(get_db)
):
    return db.query(Club).all()


@router.post("/")
def create_club(
    club: ClubCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    )
):
    existing_club = (
        db.query(Club)
        .filter(
            Club.club_name == club.club_name
        )
        .first()
    )

    if existing_club:
        raise HTTPException(
            status_code=400,
            detail="Club already exists"
        )
    db_club = Club(
        club_name=club.club_name,
        description=club.description
    )

    db.add(db_club)
    db.commit()
    db.refresh(db_club)

    return db_club

@router.get("/my-clubs")
def my_clubs(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    memberships = (
        db.query(ClubMembership)
        .filter(
            ClubMembership.user_id ==
            current_user.id,
            ClubMembership.is_active == True
        )
        .all()
    )

    club_ids = [
        m.club_id
        for m in memberships
    ]

    return (
        db.query(Club)
        .filter(
            Club.id.in_(club_ids)
        )
        .all()
    )

@router.get("/{club_id}/members")
def club_members(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    memberships = (
        db.query(
            ClubMembership
        )
        .filter(
            ClubMembership.club_id ==
            club_id,

            ClubMembership.is_active ==
            True
        )
        .all()
    )

    return memberships

@router.get("/{club_id}/events")
def club_events(
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

@router.get("/{club_id}/stats")
def club_stats(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    club = (
        db.query(Club)
        .filter(
            Club.id == club_id
        )
        .first()
    )

    if not club:
        raise HTTPException(
            status_code=404,
            detail="Club not found"
        )

    total_events = (
        db.query(Event)
        .filter(
            Event.club_id == club_id
        )
        .count()
    )

    total_records = (
        db.query(EventRecord)
        .filter(
            EventRecord.club_id == club_id
        )
        .count()
    )

    approved_events = total_records

    return {
        "club_id": club.id,
        "club_name": club.club_name,
        "total_events": total_events,
        "approved_events": approved_events,
        "repository_records": total_records
    }

@router.get("/{club_id}")
def get_club(
    club_id: int,
    db: Session = Depends(get_db)
):

    club = (
        db.query(Club)
        .filter(
            Club.id == club_id
        )
        .first()
    )

    if not club:
        raise HTTPException(
            status_code=404,
            detail="Club not found"
        )

    return club

