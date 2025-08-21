from typing import Optional, Sequence

from labstructanalyzer.schemas.template import TemplateDto, TemplateElementUpdateUnit


class TemplateToModify(TemplateDto):
    name: Optional[str] = None
    max_score: Optional[int] = None
    elements: Optional[Sequence[TemplateElementUpdateUnit]]
