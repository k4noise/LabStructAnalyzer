import unittest
import uuid
from unittest.mock import MagicMock, AsyncMock

from labstructanalyzer.repository.template import TemplateRepository
from labstructanalyzer.models.template import Template


class TestTemplateRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Настройка мок-сессии и репозитория"""
        self.session = MagicMock()
        self.session.exec = AsyncMock()
        self.session.flush = AsyncMock()
        self.session.add = MagicMock()
        self.session.delete = AsyncMock()

        self.repo = TemplateRepository(self.session)
        self.course_id = "course123"
        self.user_id = "user123"
        self.template_id = uuid.uuid4()

    async def test_create_template(self):
        """Создание черновика шаблона добавляет его в сессию и выполняет flush"""
        template = Template(
            user_id=self.user_id,
            course_id=self.course_id,
            name="Test Name"
        )

        await self.repo.create(template)

        self.session.add.assert_called_once_with(template)
        self.session.flush.assert_awaited_once()

    async def test_get_template_success(self):
        """Успешное получение шаблона"""
        mock_template = MagicMock(spec=Template)
        mock_result = MagicMock()
        mock_result.first.return_value = mock_template
        self.session.exec.return_value = mock_result

        result = await self.repo.get(self.course_id, self.template_id)

        self.session.exec.assert_awaited_once()
        mock_result.first.assert_called_once()
        self.assertEqual(result, mock_template)

    async def test_get_template_not_found(self):
        """Возврат None, если шаблон не найден"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        self.session.exec.return_value = mock_result

        result = await self.repo.get(self.course_id, self.template_id)

        self.assertIsNone(result)

    async def test_update_template(self):
        """Обновление шаблона добавляет его в сессию"""
        template = Template(
            template_id=self.template_id,
            course_id=self.course_id,
            name="Updated Name"
        )

        await self.repo.update(template)

        self.session.add.assert_called_once_with(template)

    async def test_delete_template(self):
        """Удаление шаблона"""
        template = Template(template_id=self.template_id, course_id=self.course_id)

        await self.repo.delete(template)

        self.session.delete.assert_awaited_once_with(template)

    async def test_get_all_templates_including_drafts(self):
        """Возвращает все шаблоны пользователя (вместе с черновиками)"""
        mock_templates = [MagicMock(spec=Template), MagicMock(spec=Template)]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_templates
        self.session.exec.return_value = mock_result

        result = await self.repo.get_all_by_course_user(self.course_id, self.user_id, include_drafts=True)

        self.session.exec.assert_awaited_once()
        mock_result.all.assert_called_once()
        self.assertEqual(result, mock_templates)

    async def test_get_all_templates_without_drafts(self):
        """Возвращает только опубликованные шаблоны с отчетами пользователя"""
        mock_templates = [MagicMock(spec=Template)]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_templates
        self.session.exec.return_value = mock_result

        result = await self.repo.get_all_by_course_user(self.course_id, self.user_id, include_drafts=False)

        self.session.exec.assert_awaited_once()
        mock_result.all.assert_called_once()
        self.assertEqual(result, mock_templates)
