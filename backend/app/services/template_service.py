from app.models.template import Template


class TemplateService:

    @staticmethod
    def create_template(
        db,
        version,
        schema_json,
        drive_file_id=None
    ):

        template = Template(
            version=version,
            schema_json=schema_json,
            drive_file_id=drive_file_id
        )

        db.add(template)

        db.flush()

        db.refresh(template)

        return template

    @staticmethod
    def get_latest_template(
        db
    ):
        return (
            db.query(Template)
            .order_by(
                Template.id.desc()
            )
            .first()
        )