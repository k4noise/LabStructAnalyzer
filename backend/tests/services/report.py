import unittest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

from labstructanalyzer.domain.report import UpdateGradeInfo
from labstructanalyzer.domain.report_status import ReportStatus
from labstructanalyzer.exceptions.access_denied import NotOwnerAccessDeniedException
from labstructanalyzer.exceptions.invalid_action import InvalidActionException
from labstructanalyzer.exceptions.no_entity import ReportNotFoundException
from labstructanalyzer.models.report import Report
from labstructanalyzer.models.template import Template
from labstructanalyzer.models.template_element import TemplateElement
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.schemas.answer import UpdateAnswerDataRequest, UpdateAnswerScoresRequest
from labstructanalyzer.schemas.report import ReportCreationResponse, AllReportsResponse
from labstructanalyzer.schemas.template import TemplateDetailResponse, FullWorkResponse
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.services.report import ReportService


class TestReportService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Создание мок-репозиториев, сервисов и глобального логгера"""
        self.repo = MagicMock()
        self.repo.create = AsyncMock()
        self.repo.update = AsyncMock()
        self.repo.get_last_by_author = AsyncMock()
        self.repo.get_with_template_and_answers = AsyncMock()
        self.repo.get_all_by_template = AsyncMock()

        self.answer_service = MagicMock()
        self.answer_service.create = AsyncMock()
        self.answer_service.update_data = AsyncMock()
        self.answer_service.update_scores = AsyncMock()

        self.mock_logger_instance = MagicMock()
        mock_global_logger = MagicMock()
        mock_global_logger.return_value.get_logger.return_value = self.mock_logger_instance
        patcher = patch('labstructanalyzer.services.report.GlobalLogger', mock_global_logger)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.service = ReportService(self.repo, self.answer_service)

        self.user = User(sub="user", course_id="course", roles=[UserRole.STUDENT], launch_id="launch_id")
        self.report_id = uuid.uuid4()
        self.nrps = MagicMock(spec=NrpsService)

        self.template = Template(
            id=uuid.uuid4(),
            name="template",
            course_id=self.user.course_id,
            elements=[
                TemplateElement(id=uuid.uuid4(), element_type='answer'),
                TemplateElement(id=uuid.uuid4(), element_type='text'),
            ]
        )

    async def test_create_success_no_existing(self):
        """Успешное создание отчета без предыдущего: создает новые пустые ответы"""
        self.repo.get_last_by_author.return_value = None
        self.repo.get_template.return_value = self.template

        new_report = Report(
            id=self.report_id,
            template_id=self.template.id,
            author_id=self.user.sub,
            status=ReportStatus.CREATED,
            template=self.template,
        )
        self.repo.create.return_value = new_report

        result = await self.service.create(self.user, TemplateDetailResponse.from_domain(self.template, self.user))

        self.assertIsInstance(result, ReportCreationResponse)
        self.assertNotEqual(result.id, self.report_id)
        self.repo.create.assert_awaited_once()
        self.answer_service.create.assert_awaited_once_with(result.id, unittest.mock.ANY)
        self.mock_logger_instance.info.assert_called_with(
            f"Отчет для пользователя с id {self.user.sub} создан: id {result.id} на основе шаблона с id{self.template.id}"
        )

    async def test_create_success_with_existing_graded(self):
        """Создание отчета с переносом ответов из предыдущего graded отчета"""
        existing_report = Report(
            id=uuid.uuid4(),
            status=ReportStatus.GRADED,
            answers=[MagicMock(element_id=uuid.uuid4())],
            template=self.template,
        )
        self.repo.get_last_by_author.return_value = existing_report

        new_report = Report(
            id=self.report_id,
            template_id=self.template.id,
            author_id=self.user.sub,
            status=ReportStatus.CREATED,
            template=self.template,
        )
        self.repo.create.return_value = new_report

        result = await self.service.create(self.user, TemplateDetailResponse.from_domain(self.template, self.user))

        self.assertNotEqual(result.id, self.report_id)
        self.answer_service.create.assert_awaited_once_with(result.id, unittest.mock.ANY)
        self.mock_logger_instance.info.assert_called()

    async def test_create_invalid_existing_not_graded(self):
        """Создание отчета, если существующий не graded, вызывает InvalidActionException"""
        existing_report = Report(
            id=uuid.uuid4(),
            status=ReportStatus.SAVED,
            template=self.template,
        )
        self.repo.get_last_by_author.return_value = existing_report

        with self.assertRaises(InvalidActionException):
            await self.service.create(self.user, TemplateDetailResponse.from_domain(self.template, self.user))
        self.repo.create.assert_not_awaited()
        self.answer_service.create.assert_not_awaited()

    async def test_get_success(self):
        """Успешное получение отчета с шаблоном"""
        report = Report(
            id=self.report_id,
            author_id=self.user.sub,
            status=ReportStatus.CREATED,
            template=self.template,
        )
        self.repo.get_with_template_and_answers.return_value = report

        result = await self.service.get(self.user, self.report_id, self.nrps)

        self.assertIsInstance(result, FullWorkResponse)
        self.repo.get_with_template_and_answers.assert_awaited_once_with(self.report_id, self.user.sub)

    async def test_get_not_found(self):
        """Попытка получения несуществующего отчета вызывает ReportNotFoundException"""
        self.repo.get_with_template_and_answers.return_value = None

        with self.assertRaises(ReportNotFoundException):
            await self.service.get(self.user, self.report_id, self.nrps)
        self.mock_logger_instance.info.assert_not_called()

    async def test_get_all_by_template(self):
        """Возвращает все отчеты по шаблону, кроме отчета пользователя"""
        template = TemplateDetailResponse(
            id=self.template.id,
            name="Test",
            max_score=1,
            elements=[],
            user=User(sub="1", roles=[], launch_id="1", course_id="1")
        )
        all_reports = [Report(id=uuid.uuid4(), author_id=uuid.uuid4())]
        self.repo.get_all_by_template.return_value = all_reports

        result = await self.service.get_all_by_template(template, self.user, self.nrps)
        self.assertIsInstance(result, AllReportsResponse)
        self.repo.get_all_by_template.assert_awaited_once_with(self.template.id)

    async def test_save_success(self):
        """Успешное сохранение ответов и изменение статуса на SAVED"""
        report = Report(
            id=self.report_id,
            author_id=self.user.sub,
            status=ReportStatus.CREATED,
            template=self.template,
        )
        self.repo.get_with_template_and_answers.return_value = report
        self.repo.update.return_value = report
        answers = [UpdateAnswerDataRequest(id=uuid.uuid4(), data={"new_data": 1323})]

        await self.service.save(self.user, self.report_id, answers)

        self.assertEqual(report.status, ReportStatus.SAVED)
        self.repo.update.assert_awaited_once_with(report)
        self.answer_service.update_data.assert_awaited_once_with(self.report_id, answers)
        self.mock_logger_instance.info.assert_called_with(f"Обновлены ответы в отчете: id {self.report_id}")

    async def test_submit_success(self):
        """Успешная отправка отчета на проверку"""
        report = Report(
            id=self.report_id,
            author_id=self.user.sub,
            status=ReportStatus.SAVED,
            template=self.template,
        )
        self.repo.get_with_template_and_answers.return_value = report
        self.repo.update.return_value = report

        await self.service.submit(self.user, self.report_id)

        self.assertEqual(report.status, ReportStatus.SUBMITTED)
        self.repo.update.assert_awaited_once_with(report)

    async def test_unsubmit_success(self):
        """Успешное снятие отчета с проверки"""
        report = Report(
            id=self.report_id,
            author_id=self.user.sub,
            status=ReportStatus.SUBMITTED,
            template=self.template,
        )
        self.repo.get_with_template_and_answers.return_value = report
        self.repo.update.return_value = report

        await self.service.unsubmit(self.user, self.report_id)

        self.assertEqual(report.status, ReportStatus.SAVED)
        self.repo.update.assert_awaited_once_with(report)

    async def test_grade_success(self):
        """Успешная оценка отчета"""
        report = Report(
            id=self.report_id,
            author_id=self.user.sub,
            status=ReportStatus.SUBMITTED,
            template=self.template,
        )
        self.repo.get_with_template_and_answers.return_value = report
        self.repo.update.return_value = report
        updates = UpdateGradeInfo(id=uuid.uuid4(), grader_id="g1", final_score=90,
                                  new_scores=[
                                      UpdateAnswerScoresRequest(id=self.template.elements[0].id, score=1)])

        await self.service.grade(self.user, self.report_id, updates)

        self.assertEqual(report.status, ReportStatus.GRADED)
        self.assertEqual(report.grader_id, "g1")
        self.assertEqual(report.score, 90)
        self.repo.update.assert_awaited_once_with(report)
        self.answer_service.update_scores.assert_awaited_once_with(self.report_id, updates.new_scores)

    async def test_mark_invalid_transition(self):
        """Изменение статуса на недопустимый вызывает InvalidActionException через verifier"""
        report = Report(
            id=self.report_id,
            author_id="unknown",
            status=ReportStatus.GRADED,
            template=self.template,
        )
        self.repo.get_with_template_and_answers.return_value = report

        with self.assertRaises(InvalidActionException):
            await self.service._mark(report, ReportStatus.SUBMITTED)
        self.repo.update.assert_not_awaited()

    async def test_get_invalid_access(self):
        """_get с неверным доступом вызывает исключение через verifier"""
        report = Report(
            id=self.report_id,
            author_id="unknown",
            status=ReportStatus.GRADED,
            template=self.template,
        )
        self.repo.get_with_template_and_answers.return_value = report

        with self.assertRaises(NotOwnerAccessDeniedException):
            await self.service._get(self.report_id, self.user)


if __name__ == '__main__':
    unittest.main()
