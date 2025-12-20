import uuid
from typing import Sequence, Optional

from pydantic import BaseModel

from labstructanalyzer.schemas.answer import AnswerResponse


class NewHintRequest(BaseModel):
    question_id: uuid.UUID
    current: AnswerResponse
    params: Optional[Sequence[AnswerResponse]] = None


class HintGenerationRequest(BaseModel):
    answer: str
    question: str
    theory: Sequence[str]
    error_explanation: str

    pre_score: Optional[float] = 0
