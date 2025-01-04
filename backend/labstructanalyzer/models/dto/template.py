import uuid
from typing import Optional

from pydantic import BaseModel

from labstructanalyzer.models.dto.template_element import TemplateElementDto


class TemplateMinimalProperties(BaseModel):
    template_id: uuid.UUID
    name: str

class TemplateDto(TemplateMinimalProperties):
    is_draft: bool
    max_score: int
    teacher_interface: Optional[bool] = False

    class Config:
        for_attributes = True


class TemplateWithElementsDto(TemplateDto):
    elements: list[TemplateElementDto]

    class Config:
        for_attributes = True

class AllTemplatesDto(BaseModel):
    teacher_interface: bool
    course_name: str
    templates: list[TemplateMinimalProperties]

