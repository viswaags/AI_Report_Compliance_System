from fastapi import (
    APIRouter
)

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.dependencies import (
    get_db
)

from app.models.user import User
from app.models.club import Club
from app.models.event import Event
from app.models.report import Report

router = APIRouter(
    prefix="/system",
    tags=["System"]
)

@router.get("/health")
def health():

    return {
        "status": "healthy"
    }

@router.get("/stats")
def stats(
    db: Session = Depends(
        get_db
    )
):

    return {

        "users":
            db.query(User).count(),

        "clubs":
            db.query(Club).count(),

        "events":
            db.query(Event).count(),

        "reports":
            db.query(Report).count()
    }