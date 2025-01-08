import uuid
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


class Answer(SQLModel, table=True):
    __tablename__ = 'answers'

    answer_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    report_id: uuid.UUID = Field(foreign_key="reports.report_id", index=True)
    element_id: uuid.UUID
    data: dict = Field(sa_column=Column(JSON))
    score: Optional[float]
