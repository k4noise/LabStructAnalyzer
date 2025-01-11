import uuid
from typing import Optional

from pydantic import BaseModel, Extra


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

