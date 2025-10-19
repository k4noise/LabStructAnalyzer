import uuid
from typing import Sequence

from sqlalchemy import Select
from sqlalchemy.orm import joinedload
from sqlmodel import select, col, desc
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.models.report import Report


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, report: Report):
        """Создать отчет"""
        self.session.add(report)
        await self.session.flush()

    async def get(self, report_id: uuid.UUID) -> Report | None:
        """Получить только отчет"""
        statement: Select = (
            select(Report)
            .where(Report.report_id == report_id)
        )
        report = await self.session.exec(statement)
        return report.first()

    async def get_with_template_and_answers(self, report_id: uuid.UUID, user_id: str) -> Report | None:
        """Получить отчет со всеми данными"""
        statement: Select = (
            select(Report)
            .where(Report.report_id == report_id, Report.author_id != user_id)
            .options(joinedload(Report.template))
            .options(joinedload(Report.answers))
        )
        report = await self.session.exec(statement)
        return report.first()

    async def get_last_by_author(self, author_id: str, template_id: uuid.UUID) -> Report | None:
        """Получить последний отчет по автору"""
        statement: Select = (
            select(Report)
            .where(Report.template_id == template_id,
                   col(Report.author_id) == author_id)
            .order_by(desc(Report.created_at))
            .limit(1)
        )
        report = await self.session.exec(statement)
        return report.first()

    async def get_all_by_template(self, template_id: uuid.UUID) -> Sequence[Report]:
        """Получить все отчеты по курсу"""
        statement: Select = (
            select(Report)
            .where(Report.template_id == template_id)
            .order_by(desc(Report.created_at))
        )
        report = await self.session.exec(statement)
        return report.all()

    async def update(self, report: Report):
        self.session.add(report)

    async def delete(self, report: Report):
        await self.session.delete(report)
