import enum
import uuid
from datetime import datetime

from sqlalchemy.orm import joinedload
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.exceptions.access_denied import NotOwnerAccessDeniedException
from labstructanalyzer.exceptions.no_entity import ReportNotFoundException
from labstructanalyzer.models.report import Report


class ReportStatus(enum.Enum):
    created = "Создан"
    saved = "Сохранен"
    submitted = "Отправлен на проверку"
    graded = "Проверен"


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def validate_author(self, report: Report, user_id: str) -> None:
        """
        Проверяет, является ли пользователь автором шаблона

        Raises:
            ReportNotFoundException: Отчет не найден
            NotOwnerAccessDeniedException: Доступ запрещен: пользователь не является автором
        """
        if report.author_id != user_id:
            raise NotOwnerAccessDeniedException()

    async def mark_as_saved(self, report_id: uuid.UUID, user_id: str):
        """
        Помечает отчет как сохраненный

        Raises:
            ReportNotFoundException: Отчет не найден
        """
        report = await self.get_by_id(report_id)
        self.validate_author(report, user_id)
        report.status = ReportStatus.saved.name
        return await self._save(report)

    async def submit_to_review(self, report_id: uuid.UUID, user_id: str):
        """
        Отправляет отчет на проверку

        Raises:
            ReportNotFoundException: Отчет не найден
        """
        report = await self.get_by_id(report_id)
        self.validate_author(report, user_id)
        report.status = ReportStatus.submitted.name
        return await self._save(report)

    async def cancel_review_submit(self, report_id: uuid.UUID, user_id: str):
        """
        Отменяет отправку отчета на проверку

        Raises:
            ReportNotFoundException: Отчет не найден
        """
        report = await self.get_by_id(report_id)
        self.validate_author(report, user_id)
        report.status = ReportStatus.saved.name
        return await self._save(report)

    async def create(self, template_id: uuid.UUID, user_id: str) -> uuid.UUID:
        """
        Создает новый отчет, возвращая его id.
        """
        report = Report(
            template_id=template_id,
            author_id=user_id,
            status=ReportStatus.created.name,
        )
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report.report_id

    async def get_by_id(self, report_id: uuid.UUID) -> Report:
        """
        Получить текущий отчет

        Raises:
            ReportNotFoundException: Отчет не найден
        """
        query = (
            select(Report)
            .where(Report.report_id == report_id)
            .options(joinedload(Report.template))
        )

        result = await self.session.exec(query)
        report = result.first()
        if report is None:
            raise ReportNotFoundException(report_id)
        return report

    async def get_last_by_author(self, template_id: uuid.UUID, author_id: str) -> Report:
        """
        Получает последний доступный отчет по id шаблона
        """
        query = (
            select(Report)
            .where(
                Report.author_id == author_id,
                Report.template_id == template_id,
            )
            .order_by(desc(Report.created_at))
            .limit(1)
        )

        return (await self.session.exec(query)).first()

    async def grade(self, report_id: uuid.UUID, grader_id: str, score: float):
        """
        Сохраняет оценку в отчете и изменяет его статус

        Raises:
            ReportNotFoundException: Отчет не найден
        """
        report = await self.get_by_id(report_id)
        report.score = score
        report.grader_id = grader_id
        report.status = ReportStatus.graded.name
        report.updated_at = datetime.now()
        self.session.add(report)
        await self.session.commit()

    async def _save(self, report: Report):
        report.updated_at = datetime.now()
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report
