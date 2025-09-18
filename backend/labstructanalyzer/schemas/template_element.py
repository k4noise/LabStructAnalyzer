import enum
import uuid
from collections.abc import Sequence
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from labstructanalyzer.models.template_element import TemplateElement


class TemplateElementUpdateAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class TemplateElementProperties(BaseModel):
    element_id: uuid.UUID
    properties: dict


class CreateTemplateElementRequest(TemplateElementProperties):
    element_type: str
    data: str | Sequence[TemplateElementProperties]


class TemplateElementUpdateRequest(BaseModel):
    """Операция над элементом шаблона"""
    action: TemplateElementUpdateAction
    element_id: uuid.UUID
    element_type: Optional[str] = None
    properties: Dict[str, Any] | Sequence[TemplateElementResponse] = Field(default_factory=dict)


class TemplateElementResponse(TemplateElementProperties):
    element_type: str
    parent_id: Optional[uuid.UUID] = None

    class Config:
        for_attributes = True

    @staticmethod
    def from_domain(element: TemplateElement) -> "TemplateElementResponse":
        return TemplateElementResponse(
            element_id=element.element_id,
            element_type=element.element_type,
            parent_id=element.parent_element_id,
            properties=element.properties
        )
