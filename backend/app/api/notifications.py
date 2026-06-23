from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_user
)

from app.database.dependencies import (
    get_db
)

from app.models.user import User

from app.services.notification_service import (
    NotificationService
)

from app.models.notification import Notification

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.get("/")
def my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        NotificationService
        .get_user_notifications(
            db,
            current_user.id
        )
    )

@router.get("/latest")
def latest_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        db.query(Notification)
        .filter(
            Notification.user_id ==
            current_user.id
        )
        .order_by(
            Notification.created_at.desc()
        )
        .limit(10)
        .all()
    )

@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return {
        "unread_count":
            NotificationService
            .unread_count(
                db,
                current_user.id
            )
    }

@router.get("/stats")
def notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    total = (
        NotificationService
        .get_user_notifications(
            db,
            current_user.id
        )
    )

    unread = (
        NotificationService
        .unread_count(
            db,
            current_user.id
        )
    )

    return {
        "total":
            len(total),

        "unread":
            unread,

        "read":
            len(total) - unread
    }


@router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        NotificationService
        .mark_all_as_read(
            db,
            current_user.id
        )
    )

@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    notification = (
        NotificationService
        .mark_as_read(
            db,
            notification_id,
            current_user.id
        )
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    return notification

'''from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_user
)

from app.database.dependencies import (
    get_db
)

from app.models.user import User

from app.services.notification_service import (
    NotificationService
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get("/me")
def my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        NotificationService
        .get_user_notifications(
            db,
            current_user.id
        )
    )


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return {
        "count":
        NotificationService.unread_count(
            db,
            current_user.id
        )
    }


@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    notification = (
        NotificationService
        .mark_as_read(
            db,
            notification_id,
            current_user.id
        )
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    return notification


@router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        NotificationService
        .mark_all_as_read(
            db,
            current_user.id
        )
    )
'''