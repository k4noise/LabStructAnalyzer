import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, text, FetchedValue, Index
from sqlmodel import SQLModel, Field, Relationship

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.models.template import Template


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    report_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    template_id: uuid.UUID = Field(foreign_key="templates.template_id")
    author_id: str
    status: str
    grader_id: Optional[str]
    score: Optional[float]

    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )

    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        ),
    )

    answers: list[Answer] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "joined"}
    )

    template: "Template" = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )

    __table_args__ = (
        Index("reports_template_id_updated_at_idx", "template_id", "updated_at"),
        Index(
            "reports_author_id_template_id_created_at_idx",
            "author_id",
            "template_id",
            "created_at",
        ),
    )
