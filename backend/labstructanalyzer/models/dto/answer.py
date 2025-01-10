import uuid
from typing import Optional

from pydantic import BaseModel


class CreateAnswerDto(BaseModel):
    element_id: uuid.UUID
    data: dict


class UpdateAnswerDto(BaseModel):
    answer_id: uuid.UUID
    data: dict


class UpdateScoreAnswerDto(BaseModel):
    answer_id: uuid.UUID
    score: float


class AnswerDto(CreateAnswerDto, UpdateAnswerDto):
    score: Optional[float] = None
    data: Optional[dict] = None

