import enum
import uuid

from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.models.report import Report


class ReportStatus(enum.Enum):
    saved = "Сохранен",
    submitted = "Отправлен на проверку",
    graded = "Проверен"


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_is_author(self, report_id: uuid.UUID, user_id: str) -> bool:
        """
        Проверяет, является ли пользователь автором шаблона
        """
        result = await self.session.get(Report, report_id)
        return result and result.author_id == user_id

    async def create(self, template_id: uuid.UUID, user_id: str) -> uuid.UUID:
        """
        Создает новый отчет, возвращая его id.
        """
        report = Report(
            template_id=template_id,
            author_id=user_id,
            status=ReportStatus.saved.name,
        )
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report.report_id

    async def get_by_id(self, report_id: uuid.UUID):
        """
        Получить текущий отчет
        """
        return await self.session.get(Report, report_id)

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

        return await self.session.exec(statement).first()

    async def set_grade(self, report_id: uuid.UUID, score: float):
        """
        Сохраняет оценку в отчете и изменяет его статус
        """
        report = await self.session.get(Report, report_id)
        report.score = score
        report.status = ReportStatus.graded.name
        self.session.add(report)
        await self.session.commit()
