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
    id: uuid.UUID
    properties: dict


class TemplateElementResponse(TemplateElementProperties):
    type: str
    parent_id: Optional[uuid.UUID] = None

    class Config:
        for_attributes = True

    @staticmethod
    def from_domain(element: TemplateElement) -> "TemplateElementResponse":
        return TemplateElementResponse(
            id=element.id,
            type=element.type,
            parent_id=element.parent_element_id,
            properties=element.properties or {}
        )


class CreateTemplateElementRequest(TemplateElementProperties):
    element_type: str
    data: str | Sequence[TemplateElementProperties]


class TemplateElementUpdateRequest(BaseModel):
    """Операция над элементом шаблона"""
    action: TemplateElementUpdateAction
    id: uuid.UUID
    type: Optional[str] = None
    properties: Dict[str, Any] | Sequence[TemplateElementResponse] = Field(default_factory=dict)
