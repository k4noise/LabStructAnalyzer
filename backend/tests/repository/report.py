import unittest
import uuid
from unittest.mock import MagicMock, AsyncMock

from labstructanalyzer.repository.report import ReportRepository
from labstructanalyzer.models.report import Report


class TestReportRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Настройка мок-сессии и репозитория"""
        self.session = MagicMock()
        self.session.exec = AsyncMock()
        self.session.flush = AsyncMock()
        self.session.add = MagicMock()
        self.session.delete = AsyncMock()

        self.repo = ReportRepository(self.session)
        self.report_id = uuid.uuid4()
        self.template_id = uuid.uuid4()
        self.author_id = "author123"
        self.user_id = "user123"

    async def test_create_report(self):
        """Создание отчета добавляет его в сессию и выполняет flush"""
        report = Report(
            report_id=self.report_id,
            template_id=self.template_id,
            author_id=self.author_id
        )

        await self.repo.create(report)

        self.session.add.assert_called_once_with(report)
        self.session.flush.assert_awaited_once()

    async def test_get_report_success(self):
        """Успешное получение отчета по ID"""
        mock_report = MagicMock(spec=Report)
        mock_result = MagicMock()
        mock_result.first.return_value = mock_report
        self.session.exec.return_value = mock_result

        result = await self.repo.get(self.report_id)

        self.session.exec.assert_awaited_once()
        mock_result.first.assert_called_once()
        self.assertEqual(result, mock_report)

    async def test_get_report_not_found(self):
        """Возврат None, если отчет не найден"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        self.session.exec.return_value = mock_result

        result = await self.repo.get(self.report_id)

        self.session.exec.assert_awaited_once()
        self.assertIsNone(result)

    async def test_get_with_template_and_answers_success(self):
        """Успешное получение отчета с шаблоном и ответами"""
        mock_report = MagicMock(spec=Report)
        mock_result = MagicMock()
        mock_result.first.return_value = mock_report
        self.session.exec.return_value = mock_result

        result = await self.repo.get_with_template_and_answers(self.report_id, self.user_id)

        self.session.exec.assert_awaited_once()
        mock_result.first.assert_called_once()
        self.assertEqual(result, mock_report)

    async def test_get_with_template_and_answers_not_found(self):
        """Возврат None, если отчет с шаблоном и ответами не найден"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        self.session.exec.return_value = mock_result

        result = await self.repo.get_with_template_and_answers(self.report_id, self.user_id)

        self.assertIsNone(result)

    async def test_get_last_by_author_success(self):
        """Успешное получение последнего отчета автора"""
        mock_report = MagicMock(spec=Report)
        mock_result = MagicMock()
        mock_result.first.return_value = mock_report
        self.session.exec.return_value = mock_result

        result = await self.repo.get_last_by_author(self.author_id, self.template_id)

        self.session.exec.assert_awaited_once()
        mock_result.first.assert_called_once()
        self.assertEqual(result, mock_report)

    async def test_get_last_by_author_not_found(self):
        """Возврат None, если у автора нет отчетов по данному шаблону"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        self.session.exec.return_value = mock_result

        result = await self.repo.get_last_by_author(self.author_id, self.template_id)

        self.assertIsNone(result)

    async def test_get_all_by_template_with_reports(self):
        """Возвращает все отчеты по шаблону"""
        mock_reports = [MagicMock(spec=Report), MagicMock(spec=Report)]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_reports
        self.session.exec.return_value = mock_result

        result = await self.repo.get_all_by_template(self.template_id)

        self.session.exec.assert_awaited_once()
        mock_result.all.assert_called_once()
        self.assertEqual(result, mock_reports)

    async def test_get_all_by_template_empty(self):
        """Возвращает пустой список, если отчетов по шаблону нет"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        self.session.exec.return_value = mock_result

        result = await self.repo.get_all_by_template(self.template_id)

        self.session.exec.assert_awaited_once()
        mock_result.all.assert_called_once()
        self.assertEqual(result, [])

    async def test_update_report(self):
        """Обновление отчета добавляет его в сессию"""
        report = Report(
            report_id=self.report_id,
            template_id=self.template_id,
            author_id=self.author_id
        )

        await self.repo.update(report)

        self.session.add.assert_called_once_with(report)

    async def test_delete_report(self):
        """Удаление отчета"""
        report = Report(
            report_id=self.report_id,
            template_id=self.template_id,
            author_id=self.author_id
        )

        await self.repo.delete(report)

        self.session.delete.assert_awaited_once_with(report)
