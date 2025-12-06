import uuid
from typing import Sequence, Optional

from sqlalchemy import Select
from sqlalchemy.orm import selectinload, with_loader_criteria

from sqlmodel import select, col, desc, asc
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.models.report import Report
from labstructanalyzer.models.template import Template


class TemplateRepository:
    """Управление шаблонами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, template: Template):
        """
        Создает черновик шаблона.
        Note! Элементы шаблона создаются отдельно и привязываются к шаблону по его id
        """
        self.session.add(template)
        await self.session.flush()
        return template

    async def get(self, course_id: str, template_id: uuid.UUID) -> Optional[Template]:
        """Получает шаблон по идентификатору"""
        statement: Select = (
            select(Template)
            .where(Template.id == template_id, Template.course_id == course_id)
            .options(selectinload(Template.elements))
        )

        result = await self.session.exec(statement)
        return result.first()

    async def update(self, template: Template):
        """Обновляет свойства шаблона"""
        self.session.add(template)

    async def delete(self, template: Template):
        """Удаляет шаблон по идентификатору"""
        await self.session.delete(template)

    async def get_all_by_course_user(self, course_id: str, user_id: str, include_drafts: bool = False) -> Sequence[
        Template]:
        """Получает все шаблоны (вместе с отчетами), доступные для пользователя в рамках курса.
        Если допустимо отображение черновиков шаблона, то отчеты не загружаются по умолчанию"""

        statement: Select = (
            select(Template)
            .where(Template.course_id == course_id)
            .order_by(asc(Template.is_draft), desc(Template.created_at))
        )

        if not include_drafts:
            statement = (
                statement
                .where(col(Template.is_draft).is_(False))
                .options(
                    selectinload(Template.reports),
                    with_loader_criteria(
                        Report,
                        col(Report.author_id) == user_id,
                        include_aliases=True,
                    ),
                )
            )

        result = await self.session.exec(statement)
        return result.all()
