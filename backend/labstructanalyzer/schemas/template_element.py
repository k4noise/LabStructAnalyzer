import uuid

from pydantic import BaseModel

class BaseTemplateElementDto(BaseModel):
    element_id: uuid.UUID
    properties: dict

class TemplateElementDto(BaseTemplateElementDto):
    element_type: str

    class Config:
        for_attributes = True

