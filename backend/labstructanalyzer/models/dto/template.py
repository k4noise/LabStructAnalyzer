import uuid

from pydantic import BaseModel

from labstructanalyzer.models.dto.template_element import TemplateElementDto


class TemplateDto(BaseModel):
    template_id: uuid.UUID
    name: str
    is_draft: bool
    max_score: int

    class Config:
        for_attributes = True


class TemplateWithElementsDto(TemplateDto):
    elements: list[TemplateElementDto]

    class Config:
        for_attributes = True
