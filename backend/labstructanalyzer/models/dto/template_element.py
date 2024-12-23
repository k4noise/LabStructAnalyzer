import uuid

from pydantic import BaseModel


class TemplateElementDto(BaseModel):
    element_id: uuid.UUID
    element_type: str
    properties: dict

    class Config:
        for_attributes = True

