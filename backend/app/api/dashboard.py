from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.dependencies import get_db

from app.models.user import User, UserRole
from app.models.report import Report
from app.models.event import Event
from app.models.club import Club
from app.models.event_record import EventRecord

from app.services.access_control_service import (
    AccessControlService
)
from sqlalchemy import func

from app.services.dashboard_service import (
    DashboardService
)

from app.auth.dependencies import get_current_user
from app.models.notification import Notification

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/recent-notifications")
def recent_notifications(
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

@router.get("/recent-reports")
def recent_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    if current_user.role == UserRole.ADMIN:

        return (
            db.query(Report)
            .order_by(
                Report.id.desc()
            )
            .limit(10)
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
        db.query(Report)
        .join(
            Event,
            Report.event_id == Event.id
        )
        .filter(
            Event.club_id.in_(club_ids)
        )
        .order_by(
            Report.id.desc()
        )
        .limit(10)
        .all()
    )

@router.get("/student")
def student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.STUDENT_REPRESENTATIVE
        )
    )
):

    return DashboardService.student_dashboard(
        db,
        current_user
    )


@router.get("/student/status")
def student_report_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.STUDENT_REPRESENTATIVE
        )
    )
):
    return DashboardService.student_report_status(
        db,
        current_user
    )


@router.get("/coordinator")
def coordinator_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.CLUB_COORDINATOR
        )
    )
):

    return DashboardService.coordinator_dashboard(
        db,
        current_user
    )

@router.get("/faculty")
def faculty_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.FACULTY_REPRESENTATIVE
        )
    )
):

    return DashboardService.faculty_dashboard(
        db,
        current_user
    )

@router.get("/admin")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):

    return DashboardService.admin_dashboard(
        db
    )

@router.get("/admin/report-summary")
def report_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    )
):

    return DashboardService.report_summary(
        db
    )

@router.get("/admin/club-performance")
def club_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    )
):

    return DashboardService.club_performance(
        db
    )

@router.get("/admin/repository-stats")
def repository_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    )
):

    return DashboardService.repository_stats(
        db
    )

