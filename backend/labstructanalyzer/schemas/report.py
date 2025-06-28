import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from labstructanalyzer.schemas.answer import AnswerDto, PreGradedAnswerDto


class ReportDto(BaseModel):
    template_id: uuid.UUID
    report_id: uuid.UUID
    can_edit: Optional[bool] = False
    can_grade: Optional[bool] = False
    status: str
    author_name: str
    grader_name: Optional[str] = None
    score: Optional[float] = None
    answers: list[AnswerDto | PreGradedAnswerDto]


class MinimalReportInfoDto(BaseModel):
    report_id: uuid.UUID
    date: datetime
    status: str
    author_name: str
    score: Optional[float] = None


class AllReportsDto(BaseModel):
    template_name: str
    max_score: float
    reports: list[MinimalReportInfoDto]
