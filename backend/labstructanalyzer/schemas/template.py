import uuid
from typing import Optional

from pydantic import BaseModel

from labstructanalyzer.schemas.template_element import TemplateElementDto


class TemplateMinimalProperties(BaseModel):
    template_id: uuid.UUID
    name: str
    report_id: Optional[uuid.UUID] = None
    report_status: Optional[str] = None


class TemplateDto(TemplateMinimalProperties):
    is_draft: bool
    max_score: int

    class Config:
        for_attributes = True


class TemplateWithElementsDto(TemplateDto):
    can_edit: Optional[bool] = False
    can_grade: Optional[bool] = False
    elements: list[TemplateElementDto]

    class Config:
        for_attributes = True


class AllTemplatesDto(BaseModel):
    can_upload: bool
    can_grade: bool
    course_name: str
    templates: list[TemplateMinimalProperties]
    drafts: Optional[list[TemplateMinimalProperties]] = None
