import uuid
from typing import Sequence

from sqlalchemy import Select, update
from sqlmodel import select, case, col
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.schemas.answer import UpdateAnswerDataRequest, UpdateAnswerScoresRequest, NewAnswerData


class AnswerRepository:
    """Управление ответами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_by_report(self, report_id: uuid.UUID) -> Sequence[Answer]:
        """Получить все ответы из отчета"""
        query: Select = select(Answer) \
            .where(Answer.report_id == report_id)
        result = await self.session.exec(query)
        return result.all()

    async def bulk_create(self, report_id: uuid.UUID, answers_data: Sequence[NewAnswerData]):
        """Создать новые ответы для отчета"""
        answers = [
            Answer(
                report_id=report_id,
                element_id=answer_data.element_id,
                score=answer_data.score,
                data=answer_data.data,
                pre_grade=answer_data.pre_grade
            )
            for answer_data in answers_data
        ]
        self.session.add_all(answers)
        await self.session.flush()
        return [answer.id for answer in answers]

    async def bulk_update_data(self, report_id: uuid.UUID, answers_data: Sequence[UpdateAnswerDataRequest]):
        """Массово обновить существующие ответы"""
        if not answers_data:
            return 0

        all_answer_ids = []
        data_updates = {}

        for item in answers_data:
            all_answer_ids.append(item.id)
            data_updates[item.id] = item.data

        data_case_expr = case(
            data_updates,
            value=Answer.id,
            else_=Answer.data
        )

        statement = (
            update(Answer)
            .where(
                col(Answer.id).in_(all_answer_ids),
                col(Answer.report_id) == report_id
            )
            .values(
                data=data_case_expr,
                score=0
            )
        )

        result = await self.session.execute(statement)
        return result.rowcount

    async def bulk_update_scores(self, report_id: uuid.UUID, scores: Sequence[UpdateAnswerScoresRequest]):
        """Массово обновить оценки ответов"""
        if not scores:
            return 0

        all_answer_ids = []
        score_updates = {}

        for item in scores:
            all_answer_ids.append(item.id)
            score_updates[item.id] = item.score

        score_case_expr = case(
            score_updates,
            value=Answer.id,
            else_=Answer.score
        )

        statement = (
            update(Answer)
            .where(
                col(Answer.id).in_(all_answer_ids),
                col(Answer.report_id) == report_id
            )
            .values(
                score=score_case_expr
            )
        )

        result = await self.session.execute(statement)
        return result.rowcount
