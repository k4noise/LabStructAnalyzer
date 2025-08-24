import enum
import uuid
from typing import Optional, Sequence, Dict, Any

from pydantic import BaseModel, Field

from labstructanalyzer.schemas.report import MinimalReport
from labstructanalyzer.schemas.template_element import TemplateElementDto


class TemplateElementUpdateAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class TemplateDto(BaseModel):
    """Краткое DTO шаблона без элементов"""
    template_id: uuid.UUID
    name: str
    is_draft: bool
    max_score: int

    model_config = {"from_attributes": True}


class TemplateWithElementsDto(TemplateDto):
    """DTO шаблона вместе с элементами"""
    elements: Sequence[TemplateElementDto]


class MinimalTemplate(BaseModel):
    """Шаблон в составе курса (с отчётами)"""
    template_id: uuid.UUID
    name: str
    is_draft: bool
    reports: Sequence[MinimalReport] = Field(default_factory=list)


class AllContentFromCourse(BaseModel):
    """Все шаблоны по курсу с отчетами"""
    can_upload: bool
    can_grade: bool
    course_name: str
    templates: Sequence[MinimalTemplate] = Field(default_factory=list)


class TemplateElementUpdateUnit(BaseModel):
    """Операция над элементом шаблона"""
    action: TemplateElementUpdateAction
    element_id: uuid.UUID
    element_type: Optional[str] = None
    properties: Dict[str, Any] | Sequence[TemplateElementDto] = Field(default_factory=dict)


class TemplateToModify(TemplateDto):
    name: Optional[str] = None
    max_score: Optional[int] = None
    elements: Optional[Sequence[TemplateElementUpdateUnit]]
