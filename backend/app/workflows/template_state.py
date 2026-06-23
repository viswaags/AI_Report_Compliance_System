from typing import TypedDict


class TemplateWorkflowState(TypedDict):

    db: object

    file_path: str

    version: str

    drive_file_id: str

    template_analysis: dict

    template_schema: dict

    template_validation: dict

    template_version_check: dict

    template: object