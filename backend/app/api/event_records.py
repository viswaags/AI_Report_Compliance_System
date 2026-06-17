from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.dependencies import get_db

from app.models.event_record import EventRecord
from app.models.user import User
from app.models.user import UserRole


router = APIRouter(
    prefix="/event-records",
    tags=["Event Records"]
)


@router.get("/")
def get_event_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR,
            UserRole.FACULTY_REPRESENTATIVE
        ])
    )
):
    return (
        db.query(EventRecord)
        .all()
    )