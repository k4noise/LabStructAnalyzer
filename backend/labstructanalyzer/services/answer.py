import uuid
from typing import Sequence

from labstructanalyzer.repository.answer import AnswerRepository
from labstructanalyzer.schemas.answer import UpdateAnswerDataRequest, UpdateAnswerScoresRequest, \
    NewAnswerData


class AnswerService:
    """
    Сервис для работы с ответами (включая оценки)
    """

    def __init__(self, repository: AnswerRepository):
        self.repository = repository

    async def create(self, report_id: uuid.UUID, elements: Sequence[NewAnswerData]):
        """
        Массово создает ответы
        """
        return await self.repository.bulk_create(report_id, elements)

    async def update_data(self, report_id: uuid.UUID, answers: Sequence[UpdateAnswerDataRequest]):
        """
        Массово обновляет ответы
        """
        await self.repository.bulk_update_data(report_id, answers)

    async def update_scores(self, report_id: uuid.UUID, scores: Sequence[UpdateAnswerScoresRequest]):
        """Массово обновляет оценки"""
        await self.repository.bulk_update_scores(report_id, scores)
