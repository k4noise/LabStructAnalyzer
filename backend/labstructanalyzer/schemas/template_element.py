import enum
import uuid
from collections.abc import Sequence
from typing import Optional, Dict, Any, Union

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


class CreateTemplateElementRequest(BaseModel):
    properties: dict
    type: str
    data: Optional[Union[str, Sequence["CreateTemplateElementRequest"]]]

    @staticmethod
    def from_domain(element: Dict[str, Any]) -> "CreateTemplateElementRequest":
        element_copy = element.copy()
        element_type = element_copy.pop('type', '')
        raw_data = element_copy.pop('data', None)

        properties = element_copy

        if isinstance(raw_data, list):
            processed_data = [CreateTemplateElementRequest.from_domain(item) for item in raw_data]
        else:
            processed_data = raw_data

        return CreateTemplateElementRequest(
            type=element_type,
            properties=properties,
            data=processed_data
        )


class TemplateElementUpdateRequest(BaseModel):
    """Операция над элементом шаблона"""
    action: TemplateElementUpdateAction
    id: uuid.UUID
    type: Optional[str] = None
    properties: Dict[str, Any] | Sequence[TemplateElementResponse] = Field(default_factory=dict)
