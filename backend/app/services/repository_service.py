from sqlalchemy import or_

from app.models.event_record import EventRecord


class RepositoryService:

    @staticmethod
    def get_all_records(
        db
    ):

        return (
            db.query(EventRecord)
            .order_by(
                EventRecord.event_date.desc()
            )
            .all()
        )

    @staticmethod
    def get_record(
        db,
        record_id
    ):

        return (
            db.query(EventRecord)
            .filter(
                EventRecord.id == record_id
            )
            .first()
        )

    @staticmethod
    def search_records(
        db,
        query=None,
        category=None,
        venue=None
    ):

        records = db.query(EventRecord)

        if query:

            records = records.filter(
                EventRecord.event_title.ilike(
                    f"%{query}%"
                )
            )

        if category:

            records = records.filter(
                EventRecord.event_category.ilike(
                    f"%{category}%"
                )
            )

        if venue:

            records = records.filter(
                EventRecord.venue.ilike(
                    f"%{venue}%"
                )
            )

        return records.all()

    @staticmethod
    def repository_stats(
        db
    ):

        total_records = (
            db.query(EventRecord)
            .count()
        )

        total_participants = sum(
            record.participant_count or 0
            for record in (
                db.query(EventRecord)
                .all()
            )
        )

        return {
            "total_records":
                total_records,

            "total_participants":
                total_participants
        }
    
    @staticmethod
    def records_by_club(
        db,
        club_id
    ):

        return (
            db.query(EventRecord)
            .filter(
                EventRecord.club_id == club_id
            )
            .order_by(
                EventRecord.event_date.desc()
            )
            .all()
        )
    
    @staticmethod
    def records_by_category(
        db,
        category
    ):

        return (
            db.query(EventRecord)
            .filter(
                EventRecord.event_category == category
            )
            .all()
        )