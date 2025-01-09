import uuid

from pydantic import BaseModel


class CreateAnswerDto(BaseModel):
    element_id: uuid.UUID
    data: dict


class UpdateAnswerDto(BaseModel):
    answer_id: uuid.UUID
    data: dict


class AnswerDto(CreateAnswerDto, UpdateAnswerDto):
    pass


class UpdateScoreAnswerDto(BaseModel):
    answer_id: uuid.UUID
    score: float
