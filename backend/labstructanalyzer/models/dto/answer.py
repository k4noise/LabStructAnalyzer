import uuid
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.models.answer_type import AnswerType


class CreateAnswerDto(BaseModel):
    element_id: uuid.UUID
    data: dict


class UpdateAnswerDto(BaseModel):
    answer_id: uuid.UUID
    data: Optional[dict] = None


class UpdateScoreAnswerDto(BaseModel):
    answer_id: uuid.UUID
    score: float


class AnswerDto(CreateAnswerDto, UpdateAnswerDto):
    score: Optional[float] = None
    data: Optional[dict] = None


class PreGradedAnswerDto(AnswerDto):
    pre_grade: Optional[dict] = None


class FullAnswerData(BaseModel):
    user_origin: Answer
    type: AnswerType
    custom_id: Optional[str] = None
    reference: Optional[str] = None
    weight: float = None


@dataclass
class GradeResult:
    score: int
    comment: str | None = None
