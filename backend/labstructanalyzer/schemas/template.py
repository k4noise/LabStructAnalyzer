import enum
import uuid
from dataclasses import field
from datetime import datetime
from typing import Optional, Sequence, Dict, Any

from pydantic import BaseModel

from labstructanalyzer.schemas.template_element import TemplateElementDto


class TemplateMinimalProperties(BaseModel):
    template_id: uuid.UUID
    name: str


class TemplateDto(TemplateMinimalProperties):
    is_draft: bool
    max_score: int

    class Config:
        for_attributes = True


class TemplateWithElementsDto(TemplateDto):
    elements: list[TemplateElementDto]

    class Config:
        for_attributes = True


class AllTemplatesDto(BaseModel):
    can_upload: bool
    can_grade: bool
    course_name: str
    templates: list[TemplateMinimalProperties]
    drafts: Optional[list[TemplateMinimalProperties]] = None


class MinimalReport(BaseModel):
    updated_at: datetime
    report_id: uuid.UUID
    status: str


class MinimalTemplate(BaseModel):
    template_id: uuid.UUID
    name: str
    is_draft: bool
    reports: Optional[Sequence[MinimalReport]]


class AllContentFromCourse(BaseModel):
    can_upload: bool
    can_grade: bool
    course_name: str
    templates: Sequence[MinimalTemplate]


class TemplateElementUpdateAction(enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class TemplateElementUpdateUnit(BaseModel):
    action: TemplateElementUpdateAction
    element_id: uuid.UUID
    element_type: Optional[str] = None
    properties: Optional[Dict[str, Any] | Sequence[TemplateElementDto]] = field(default_factory=dict)
