from app.models.template import Template


class TemplateService:

    @staticmethod
    def create_template(
        db,
        version,
        schema_json
    ):
        template = Template(
            version=version,
            schema_json=schema_json
        )

        db.add(template)
        db.commit()
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
