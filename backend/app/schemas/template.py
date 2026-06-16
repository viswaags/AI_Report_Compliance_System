from typing import Dict, Any

from pydantic import BaseModel, ConfigDict, Field


class TemplateCreate(BaseModel):
    version: str
    template_schema: Dict[str, Any]


class TemplateResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    id: int
    version: str
    template_schema: Dict[str, Any] = Field(alias="schema_json")


class TemplateAnalyzeResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )

    version: str
    template_schema: Dict[str, Any] = Field(alias="schema_json")
