import uuid
from typing import Optional

from sqlalchemy import Index, Column, JSON
from sqlmodel import SQLModel, Field


class TemplateElement(SQLModel, table=True):
    __tablename__ = 'template_elements'

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    template_id: uuid.UUID = Field(foreign_key="templates.id", nullable=False, index=True, ondelete="CASCADE")
    type: str = Field(max_length=255)
    order: int
    properties: dict = Field(sa_column=Column(JSON))
    parent_element_id: Optional[uuid.UUID] = None

    __table_args__ = (
        Index("template_element_templates_id_order_idx", "template_id", "order"),
        Index("idx_template_type", "template_id", "type"),
        Index("idx_template_id", "template_id", "id"),
    )
