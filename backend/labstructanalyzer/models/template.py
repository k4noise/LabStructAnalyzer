import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Column, TIMESTAMP, text, FetchedValue, Index
from sqlmodel import SQLModel, Field, Relationship, asc
from labstructanalyzer.models.template_element import TemplateElement


class Template(SQLModel, table=True):
    __tablename__ = 'templates'

    template_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: str = Field(max_length=255)
    user_id: str = Field(max_length=255)
    name: str = Field(max_length=255)
    is_draft: bool = Field(default=True)
    max_score: int = Field(default=20)

    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ))

    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )

    elements: List[TemplateElement] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "joined",
            "order_by": asc(TemplateElement.order)
        }
    )

    __table_args__ = (
        Index("templates_template_id_is_draft_idx", "template_id", "is_draft"),
    )

