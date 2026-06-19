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

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
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

    reports = (
        db.query(Report)
        .filter(
            Report.created_by == current_user.id
        )
        .order_by(
            Report.id.desc()
        )
        .all()
    )

    report_list = []

    for report in reports:

        event = (
            db.query(Event)
            .filter(
                Event.id == report.event_id
            )
            .first()
        )

        report_list.append(
            {
                "report_id": report.id,
                "event_title":
                    event.event_title if event else None,
                "status": report.status,
                "current_version":
                    report.current_version
            }
        )

    return {

        "total_reports":
            len(reports),

        "approved":
            len([
                r for r in reports
                if r.status == "APPROVED"
            ]),

        "under_review":
            len([
                r for r in reports
                if r.status == "UNDER_REVIEW"
            ]),

        "compliance_passed":
            len([
                r for r in reports
                if r.status == "COMPLIANCE_PASSED"
            ]),

        "correction_required":
            len([
                r for r in reports
                if r.status == "CORRECTION_REQUIRED"
            ]),

        "reports":
            report_list
    }


@router.get("/student/status")
def student_report_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.STUDENT_REPRESENTATIVE
        )
    )
):

    reports = (
        db.query(Report)
        .filter(
            Report.created_by == current_user.id
        )
        .order_by(
            Report.id.desc()
        )
        .all()
    )

    result = []

    for report in reports:

        event = (
            db.query(Event)
            .filter(
                Event.id == report.event_id
            )
            .first()
        )

        result.append(
            {
                "report_id": report.id,
                "event_title":
                    event.event_title if event else None,
                "status": report.status,
                "version": report.current_version
            }
        )

    return result


@router.get("/coordinator")
def coordinator_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR
        ])
    )
):

    if current_user.role == UserRole.ADMIN:

        reports = (
            db.query(Report)
            .all()
        )

        pending_review_reports = []

        for report in reports:

            if report.status == "COMPLIANCE_PASSED":

                event = (
                    db.query(Event)
                    .filter(
                        Event.id == report.event_id
                    )
                    .first()
                )

                pending_review_reports.append(
                    {
                        "report_id": report.id,
                        "event_title":
                            event.event_title if event else None,
                        "status": report.status
                    }
                )

        return {

            "managed_clubs":
                db.query(Club).count(),

            "pending_reviews":
                len(pending_review_reports),

            "approved_reports":
                len([
                    r for r in reports
                    if r.status == "APPROVED"
                ]),

            "pending_review_reports":
                pending_review_reports
        }

    club_ids = (
        AccessControlService
        .get_accessible_club_ids(
            db,
            current_user.id
        )
    )

    events = (
        db.query(Event)
        .filter(
            Event.club_id.in_(club_ids)
        )
        .all()
    )

    event_ids = [
        event.id
        for event in events
    ]

    reports = (
        db.query(Report)
        .filter(
            Report.event_id.in_(event_ids)
        )
        .all()
    )

    pending_review_reports = []

    for report in reports:

        if report.status == "COMPLIANCE_PASSED":

            event = (
                db.query(Event)
                .filter(
                    Event.id == report.event_id
                )
                .first()
            )

            pending_review_reports.append(
                {
                    "report_id": report.id,
                    "event_title":
                        event.event_title if event else None,
                    "status": report.status
                }
            )

    return {

        "managed_clubs":
            len(club_ids),

        "pending_reviews":
            len(pending_review_reports),

        "approved_reports":
            len([
                r for r in reports
                if r.status == "APPROVED"
            ]),

        "pending_review_reports":
            pending_review_reports
    }


@router.get("/admin")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):

    return {

        "total_users":
            db.query(User).count(),

        "total_clubs":
            db.query(Club).count(),

        "total_events":
            db.query(Event).count(),

        "total_reports":
            db.query(Report).count(),

        "approved_reports":
            db.query(Report)
            .filter(
                Report.status == "APPROVED"
            )
            .count(),

        "repository_records":
            db.query(EventRecord)
            .count()
    }