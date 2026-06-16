from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.dependencies import get_db
from app.models.club import Club
from app.models.user import User, UserRole
from app.schemas.club import ClubCreate

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
    db_club = Club(
        club_name=club.club_name,
        description=club.description
    )

    db.add(db_club)
    db.commit()
    db.refresh(db_club)

    return db_club