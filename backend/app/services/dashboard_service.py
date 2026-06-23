from sqlalchemy import func

from app.models.user import User
from app.models.club import Club
from app.models.event import Event
from app.models.report import Report
from app.models.event_record import EventRecord
from app.models.notification import Notification

from app.services.access_control_service import (
    AccessControlService
)


class DashboardService:

    @staticmethod
    def student_dashboard(
        db,
        current_user
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
                        event.event_title
                        if event else None,

                    "status":
                        report.status,

                    "current_version":
                        report.current_version
                }
            )

        unread_notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id ==
                current_user.id,

                Notification.is_read ==
                False
            )
            .count()
        )

        return {

            "total_reports":
                len(reports),

            "approved":
                len([
                    r for r in reports
                    if r.status == "APPROVED"
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

            "revision_required":
                len([
                    r for r in reports
                    if r.status == "REVISION_REQUIRED"
                ]),

            "unread_notifications":
                unread_notifications,

            "reports":
                report_list
        }

    @staticmethod
    def student_report_status(
        db,
        current_user
    ):

        reports = (
            db.query(Report)
            .filter(
                Report.created_by ==
                current_user.id
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
                    "report_id":
                        report.id,

                    "event_title":
                        event.event_title
                        if event else None,

                    "status":
                        report.status,

                    "version":
                        report.current_version
                }
            )

        return result

    @staticmethod
    def coordinator_dashboard(
        db,
        current_user
    ):

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
                        "report_id":
                            report.id,

                        "event_title":
                            event.event_title
                            if event else None,

                        "status":
                            report.status
                    }
                )

        unread_notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id ==
                current_user.id,

                Notification.is_read ==
                False
            )
            .count()
        )

        return {

            "managed_clubs":
                len(club_ids),

            "pending_reviews":
                len(
                    pending_review_reports
                ),

            "approved_reports":
                len([
                    r for r in reports
                    if r.status == "APPROVED"
                ]),

            "unread_notifications":
                unread_notifications,

            "pending_review_reports":
                pending_review_reports
        }

    @staticmethod
    def faculty_dashboard(
        db,
        current_user
    ):

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
            .count()
        )

        reports = (
            db.query(Report)
            .join(
                Event,
                Report.event_id == Event.id
            )
            .filter(
                Event.club_id.in_(club_ids)
            )
            .count()
        )

        records = (
            db.query(EventRecord)
            .filter(
                EventRecord.club_id.in_(club_ids)
            )
            .count()
        )

        unread_notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id ==
                current_user.id,

                Notification.is_read ==
                False
            )
            .count()
        )

        return {
            "clubs":
                len(club_ids),

            "events":
                events,

            "reports":
                reports,

            "records":
                records,

            "unread_notifications":
                unread_notifications
        }

    @staticmethod
    def admin_dashboard(
        db
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
                    Report.status ==
                    "APPROVED"
                )
                .count(),

            "repository_records":
                db.query(EventRecord)
                .count(),

            "total_notifications":
                db.query(Notification)
                .count()
        }
    
    @staticmethod
    def report_summary(
        db
    ):

        total_reports = (
            db.query(Report)
            .count()
        )

        approved = (
            db.query(Report)
            .filter(
                Report.status == "APPROVED"
            )
            .count()
        )

        revision_required = (
            db.query(Report)
            .filter(
                Report.status == "REVISION_REQUIRED"
            )
            .count()
        )

        correction_required = (
            db.query(Report)
            .filter(
                Report.status == "CORRECTION_REQUIRED"
            )
            .count()
        )

        compliance_passed = (
            db.query(Report)
            .filter(
                Report.status == "COMPLIANCE_PASSED"
            )
            .count()
        )

        approval_rate = 0

        if total_reports > 0:

            approval_rate = round(
                (approved / total_reports) * 100,
                2
            )

        return {
            "total_reports": total_reports,
            "approved": approved,
            "revision_required": revision_required,
            "correction_required": correction_required,
            "compliance_passed": compliance_passed,
            "approval_rate": approval_rate
        }
    
    @staticmethod
    def club_performance(
        db
    ):

        clubs = (
            db.query(Club)
            .all()
        )

        result = []

        for club in clubs:

            total_events = (
                db.query(Event)
                .filter(
                    Event.club_id == club.id
                )
                .count()
            )

            approved_records = (
                db.query(EventRecord)
                .filter(
                    EventRecord.club_id == club.id
                )
                .count()
            )

            approval_rate = 0

            if total_events > 0:

                approval_rate = round(
                    (approved_records / total_events) * 100,
                    2
                )

            result.append(
                {
                    "club_id": club.id,
                    "club_name": club.club_name,
                    "total_events": total_events,
                    "approved_events": approved_records,
                    "approval_rate": approval_rate
                }
            )

        return result
    
    @staticmethod
    def repository_stats(
        db
    ):

        total_records = (
            db.query(EventRecord)
            .count()
        )

        total_participants = (
            db.query(
                func.sum(
                    EventRecord.participant_count
                )
            )
            .scalar()
        )

        return {
            "repository_records":
                total_records,

            "total_participants":
                total_participants or 0
        }