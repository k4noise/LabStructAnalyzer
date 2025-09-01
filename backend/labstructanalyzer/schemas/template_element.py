import enum
import uuid
from collections.abc import Sequence
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class TemplateElementUpdateAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class BaseTemplateElementDto(BaseModel):
    element_id: uuid.UUID
    properties: dict


class TemplateElementDto(BaseTemplateElementDto):
    element_type: str
    parent_id: Optional[uuid.UUID] = None

    class Config:
        for_attributes = True


class CreateTemplateElementDto(BaseTemplateElementDto):
    element_type: str
    data: str | Sequence[BaseTemplateElementDto]


class TemplateElementUpdateUnit(BaseModel):
    """Операция над элементом шаблона"""
    action: TemplateElementUpdateAction
    element_id: uuid.UUID
    element_type: Optional[str] = None
    properties: Dict[str, Any] | Sequence[TemplateElementDto] = Field(default_factory=dict)
