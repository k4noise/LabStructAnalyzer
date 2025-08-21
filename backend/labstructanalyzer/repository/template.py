import uuid
from typing import Sequence, Optional

from sqlalchemy import Select, update, delete
from sqlalchemy.orm import selectinload, with_loader_criteria

from sqlmodel import select, col, desc, asc
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.domain.template import CreateTemplate, UpdateTemplate
from labstructanalyzer.models.report import Report
from labstructanalyzer.models.template import Template


class TemplateRepository:
    """Управление шаблонами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, base_template: CreateTemplate) -> Template:
        """
        Создает черновик шаблона.
        Note! Элементы шаблона создаются отдельно и привязываются к шаблону по его id

        Args:
            base_template: свойства шаблона

        Returns:
            Сохраненный шаблон
        """
        template = Template(
            user_id=base_template.user_id,
            course_id=base_template.course_id,
            name=base_template.name,
        )
        self.session.add(template)
        return template

    async def get(self, course_id: str, template_id: uuid.UUID) -> Optional[Template]:
        """Получает шаблон по идентификатору"""
        statement: Select = (
            select(Template)
            .where(Template.template_id == template_id, Template.course_id == course_id)
            .options(selectinload(Template.elements))
        )

        result = await self.session.exec(statement)
        return result.first()

    async def update(self, course_id: str, template_updates: UpdateTemplate):
        """
        Обновляет свойства шаблона

        Args:
            template_updates: свойства к обновлению, должны содержать идентификатор

        Returns:
            True, если шаблон был обновлен, иначе False
        """
        values = template_updates.model_dump(
            exclude={"id"},
            exclude_defaults=True,
        )

        if not values:
            return False

        statement = (
            update(Template)
            .where(col(Template.template_id) == template_updates.id, col(Template.course_id) == course_id)
            .values(values)
        )

        result = await self.session.execute(statement)
        return result.rowcount > 0

    async def delete(self, course_id: str, template_id: uuid.UUID):
        """Удаляет шаблон по идентификатору"""
        result = await self.session.execute(
            delete(Template)
            .where(col(Template.template_id) == template_id, col(Template.course_id) == course_id)
        )
        return result.rowcount > 0

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
