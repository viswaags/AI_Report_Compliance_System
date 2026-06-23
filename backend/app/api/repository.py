from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.dependencies import get_db
from app.models.user import User, UserRole
from app.auth.dependencies import get_current_user, require_role
from app.services.repository_service import RepositoryService


router = APIRouter(
    prefix="/repository",
    tags=["Repository"]
)


@router.get("/events")
def repository_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        RepositoryService
        .get_all_records(db)
    )

@router.get("/event/{record_id}")
def repository_event_details(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    record = (
        RepositoryService
        .get_record(
            db,
            record_id
        )
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail="Record not found"
        )

    return record

@router.get("/search")
def repository_search(
    query: str | None = None,
    category: str | None = None,
    venue: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        RepositoryService
        .search_records(
            db=db,
            query=query,
            category=category,
            venue=venue
        )
    )

@router.get("/stats")
def repository_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):

    return (
        RepositoryService
        .repository_stats(db)
    )

@router.get("/club/{club_id}")
def club_records(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        RepositoryService
        .records_by_club(
            db,
            club_id
        )
    )

@router.get(
    "/event-category/{category}"
)
def category_records(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        RepositoryService
        .records_by_category(
            db,
            category
        )
    )