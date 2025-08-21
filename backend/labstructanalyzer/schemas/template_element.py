import uuid
from collections.abc import Sequence
from typing import Optional

from pydantic import BaseModel


class BaseTemplateElementDto(BaseModel):
    element_id: uuid.UUID
    properties: dict


class TemplateElementDto(BaseTemplateElementDto):
    element_type: str
    parent_id: Optional[uuid.UUID]

    class Config:
        for_attributes = True


class CreateTemplateElementDto(BaseTemplateElementDto):
    element_type: str
    data: str | Sequence[BaseTemplateElementDto]
