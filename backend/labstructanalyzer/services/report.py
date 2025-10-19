import uuid
from datetime import datetime

from sqlalchemy import Sequence

from labstructanalyzer.core.logger import GlobalLogger
from labstructanalyzer.domain.report import UpdateGradeInfo, ReportAccessVerifier
from labstructanalyzer.domain.report_status import ReportStatus
from labstructanalyzer.exceptions.invalid_action import InvalidActionException
from labstructanalyzer.exceptions.no_entity import ReportNotFoundException
from labstructanalyzer.models.report import Report
from labstructanalyzer.models.user_model import User
from labstructanalyzer.repository.report import ReportRepository
from labstructanalyzer.schemas.answer import UpdateAnswerDataRequest, NewAnswerData
from labstructanalyzer.schemas.report import ReportCreationResponse, AllReportsResponse
from labstructanalyzer.schemas.template import TemplateDetailResponse, FullWorkResponse
from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.services.lti.nrps import NrpsService


class ReportService:
    def __init__(self, repository: ReportRepository, answer_service: AnswerService
                 ):
        self.repository = repository
        self.answer_service = answer_service
        self.logger = GlobalLogger().get_logger(__name__)

    async def create(self, user: User, template: TemplateDetailResponse):
        """Создает новый отчет, инициализирует ответы - переносит из старого отчета или создает новые пустые"""
        current_report = await self.repository.get_last_by_author(user.sub, template.id)
        if current_report and current_report.status is not ReportStatus.GRADED:
            raise InvalidActionException("отчет уже существует")
        current_answers = {answer.element_id: answer for answer in current_report.answers} if current_report else {}

        new_report = Report(
            template_id=template.id,
            author_id=user.sub,
            status=ReportStatus.CREATED,
        )
        await self.repository.create(new_report)
        await self.answer_service.create(new_report.id, [
            NewAnswerData.from_domain(element, current_answers[
                element.id] if current_report and element.id in current_answers else None)
            for element in template.elements if element.type == 'answer'
        ])
        self.logger.info(
            f"Отчет для пользователя с id {user.sub} создан: id {new_report.id} на основе шаблона с id{template.id}")
        return ReportCreationResponse(id=new_report.id)

    async def get(self, user: User, report_id: uuid.UUID, nrps: NrpsService) -> FullWorkResponse:
        """Получить отчет вместе с шаблоном"""
        report = await self._get(report_id, user)
        return FullWorkResponse.from_domain(report, user, nrps)

    async def get_all_by_template(self, template: TemplateDetailResponse, user: User,
                                  nrps: NrpsService) -> AllReportsResponse:
        """Возвращает краткую информацию о всех отчетах шаблона, кроме отчетов запросившего"""
        all_reports = await self.repository.get_all_by_template(template.id)
        return AllReportsResponse.from_domain(template, all_reports, user, nrps)

    async def save(self, user: User, report_id: uuid.UUID, answers: Sequence[UpdateAnswerDataRequest]):
        """Сохранить ответы в отчете"""
        report = await self._get(report_id, user)
        await self._mark(report, ReportStatus.SAVED)
        await self.answer_service.update_data(report_id, answers)
        self.logger.info(f"Обновлены ответы в отчете: id {report_id}")

    async def submit(self, user: User, report_id: uuid.UUID):
        """Отправить отчет на проверку"""
        report = await self._get(report_id, user)
        return await self._mark(report, ReportStatus.SUBMITTED)

    async def unsubmit(self, user: User, report_id: uuid.UUID):
        """Убрать отчет с проверки"""
        report = await self._get(report_id, user)
        return await self._mark(report, ReportStatus.SAVED)

    async def grade(self, user: User, report_id: uuid.UUID, report_updates: UpdateGradeInfo):
        """Оценить отчет"""
        report = await self._get(report_id, user)
        report.grader_id = report_updates.grader_id
        report.score = report_updates.final_score
        await self._mark(report, ReportStatus.GRADED)
        await self.answer_service.update_scores(report_id, report_updates.new_scores)

    async def _get(self, report_id: uuid.UUID, user: User) -> Report:
        """Получить модель отчета с минимальной валидацией"""
        report = await self.repository.get_with_template_and_answers(report_id, user.sub)
        if report is None:
            raise ReportNotFoundException(report_id)

        ReportAccessVerifier(report).is_valid_context(user)
        return report

    async def _mark(self, report: Report, status: ReportStatus):
        """Изменить статус отчета"""
        ReportAccessVerifier(report).is_valid_transition(status)
        report.status = status
        report.updated_at = datetime.now()
        return await self.repository.update(report)
