import uuid

from sqlalchemy import update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.models.dto.answer import UpdateScoreAnswerDto, UpdateAnswerDto, FullAnswerData
from labstructanalyzer.models.report import Report
from labstructanalyzer.models.template import Template
from labstructanalyzer.models.template_element import TemplateElement


class AnswerService:
    """
    Сервис для работы с ответами (включая оценки)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_answers(self, template: Template, report_id: uuid.UUID):
        """
        Массово создает пустые ответы
        """
        answers = [
            Answer(
                template_id=template.template_id,
                report_id=report_id,
                element_id=element.element_id,
                score=None,
                data=None
            )
            for element in template.elements if element.element_type == 'answer'
        ]

        self.session.add_all(answers)
        await self.session.commit()

    async def update_answers(self, report_id: uuid.UUID, answers: list[UpdateAnswerDto]):
        """
        Массово обновляет ответы
        """
        for update_answer in answers:
            statement = (
                update(Answer)
                .where(Answer.report_id == report_id, Answer.answer_id == update_answer.answer_id)
                .values(data=update_answer.data, score=None)
            )
            await self.session.exec(statement)
        await self.session.commit()

    async def bulk_update_grades(self, report_id: uuid.UUID, grades_data: list[UpdateScoreAnswerDto]):
        """
        Массово обновляет оценки
        """
        for grade_data in grades_data:
            statement = (
                update(Answer)
                .where(Answer.report_id == report_id, Answer.answer_id == grade_data.answer_id)
                .values(score=grade_data.score)
            )
            await self.session.exec(statement)
        await self.session.commit()

    async def calc_final_score(self, report_id: uuid.UUID, max_score: int):
        """
        Вычислить итоговый балл отчета
        """
        query = (
            select(Answer.score, TemplateElement.properties)
            .select_from(Answer)
            .join(TemplateElement, Answer.element_id == TemplateElement.element_id)
            .where(Answer.report_id == report_id)
        )
        results = await self.session.exec(query)

        weight_sum = 0
        score_with_weight_sum = 0

        for score, properties in results.all():
            weight = properties.get("weight")
            weight_sum += weight
            score_with_weight_sum += score * weight

        if score_with_weight_sum == 0:
            return 0
        return round((score_with_weight_sum / weight_sum) * max_score, 2)

    def collect_full_data(self, report: Report):
        answer_elements = {template_element.element_id: template_element for template_element in
                           report.template.elements if
                           template_element.element_type == 'answer'}
        answers_to_grade = []
        for answer in report.answers:
            if element := answer_elements.get(answer.element_id):
                answers_to_grade.append(
                    FullAnswerData(
                        user_origin=answer,
                        custom_id=element.properties.get("customId"),
                        reference=element.properties.get("refAnswer"),
                        weight=element.properties.get("weight")
                    )
                )
        return answers_to_grade
