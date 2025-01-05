import uuid
from typing import Optional

from labstructanalyzer.models.dto.template import TemplateDto
from labstructanalyzer.models.dto.template_element import TemplateElementDto, BaseTemplateElementDto


class TemplateToModify(TemplateDto):
    template_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    max_score: Optional[int] = None
    elements: Optional[list[TemplateElementDto]] = None

    updated_elements: Optional[list[BaseTemplateElementDto]] = None
    deleted_elements: Optional[list[TemplateElementDto]] = None
