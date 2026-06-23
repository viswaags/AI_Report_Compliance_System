from app.services.template_service import (
    TemplateService
)

from app.models.user import (
    User,
    UserRole
)
from app.services.notification_service import (
    NotificationService
)


class WorkflowTemplateStorageAgent:

    @staticmethod
    def run(state):

        template = (
            TemplateService
            .create_template(
                db=state["db"],
                version=state["version"],
                schema_json=
                    state[
                        "template_analysis"
                    ],
                drive_file_id=
                    state.get(
                        "drive_file_id"
                    )
            )
        )

        state["template"] = template

        coordinators = (
            state["db"]
            .query(User)
            .filter(
                User.role ==
                UserRole.CLUB_COORDINATOR,
                User.is_active == True
            )
            .all()
        )
        
        for coordinator in coordinators:

            NotificationService.create_notification(
                db=state["db"],
                user_id=coordinator.id,
                title="New Template Available",
                message=(
                    f"Template version "
                    f"{template.version} "
                    f"has been uploaded."
                ),
                notification_type="TEMPLATE"
            )

        print("Template storage completed.")

        return state