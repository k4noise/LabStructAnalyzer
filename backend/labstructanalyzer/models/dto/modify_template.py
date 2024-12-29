from typing import Optional

from labstructanalyzer.models.dto.template import TemplateDto
from labstructanalyzer.models.dto.template_element import TemplateElementDto


class TemplateToModify(TemplateDto):
    name: Optional[str] = None
    max_score: Optional[int] = None
    elements: Optional[list[TemplateElementDto]] = None

    deleted_elements: Optional[list[TemplateElementDto]] = None
    updated_elements: Optional[list[TemplateElementDto]] = None

    class Config:
        for_attributes = True

