import enum
import uuid
from datetime import datetime

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

    def check_is_author(self, report: Report, user_id: str) -> None:
        """
        Проверяет, является ли пользователь автором шаблона

        Raises:
            ReportNotFoundException: Отчет не найден
            NotOwnerAccessDeniedException: Доступ запрещен: пользователь не является автором
        """
        if report.author_id != user_id:
            raise NotOwnerAccessDeniedException()

    async def send_to_save(self, report: Report, user: str):
        """
        Отправляет отчет на проверку

        Raises:
            ReportNotFoundException: Отчет не найден
        """
        self.check_is_author(report, user)
        report.status = ReportStatus.saved.name
        report.updated_at = datetime.now()
        self.session.add(report)
        await self.session.commit()

    async def send_to_grade(self, report: Report, user: str):
        """
        Отправляет отчет на проверку

        Raises:
            ReportNotFoundException: Отчет не найден
        """
        self.check_is_author(report, user)
        report.status = ReportStatus.submitted.name
        report.updated_at = datetime.now()
        self.session.add(report)
        await self.session.commit()

    async def cancel_send_to_grade(self, report: Report, user: str):
        """
        Отменяет отправку отчета на проверку

        Raises:
            ReportNotFoundException: Отчет не найден
        """
        self.check_is_author(report, user)
        report.status = ReportStatus.saved.name
        self.session.add(report)
        report.updated_at = datetime.now()
        await self.session.commit()

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

    async def get_by_id(self, report_id: uuid.UUID):
        """
        Получить текущий отчет

        Raises:
            ReportNotFoundException: Отчет не найден
        """
        report = await self.session.get(Report, report_id)
        if report is None:
            raise ReportNotFoundException(report_id)
        return report

    async def get_prev_report(self, report: Report):
        """
        Получает отчет, предшествующий переданному
        """
        current_created_at = report.created_at
        author_id = report.author_id
        template_id = report.template_id

        statement = (
            select(Report)
            .where(
                Report.author_id == author_id,
                Report.template_id == template_id,
                Report.created_at < current_created_at,
                Report.report_id != report.report_id
            )
            .order_by(desc(Report.created_at))
            .limit(1)
        )

        return (await self.session.exec(statement)).first()

    async def set_grade(self, report_id: uuid.UUID, grader_id: str, score: float):
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
