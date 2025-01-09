import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from labstructanalyzer.models.dto.answer import AnswerDto
from labstructanalyzer.models.dto.template import TemplateDto


class ReportDto(BaseModel):
    template: TemplateDto
    report_id: uuid.UUID
    status: str
    grader_name: Optional[str] = None
    current_answers: list[AnswerDto]
    prev_answers: Optional[list[AnswerDto]] = None


class MinimalReportInfoDto(BaseModel):
    report_id: uuid.UUID
    date: datetime
    status: str
    author_name: str
    grade: Optional[float] = None