import unittest
import uuid
from unittest.mock import MagicMock, AsyncMock

from labstructanalyzer.domain.template import CreateTemplate, UpdateTemplate
from labstructanalyzer.repository.template import TemplateRepository
from labstructanalyzer.models.template import Template


class TestTemplateRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Настройка мок-сессии и репозитория"""
        self.session = MagicMock()
        self.session.exec = AsyncMock()
        self.session.execute = AsyncMock()
        self.session.add = MagicMock()

        self.repo = TemplateRepository(self.session)
        self.course_id = "course123"
        self.user_id = "user123"
        self.template_id = uuid.uuid4()

    async def test_create_template(self):
        """Создание черновика шаблона добавляет его в сессию и возвращает"""
        data = CreateTemplate(user_id=self.user_id, course_id=self.course_id, name="Test Name")
        result = await self.repo.create(data)

        self.session.add.assert_called_once_with(result)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.course_id, self.course_id)
        self.assertEqual(result.name, "Test Name")

    async def test_get_template_success(self):
        """Успешное получение шаблона"""
        mock_template = MagicMock(spec=Template)
        mock_result = MagicMock()
        mock_result.first.return_value = mock_template
        self.session.exec.return_value = mock_result

        result = await self.repo.get(self.course_id, self.template_id)

        self.session.exec.assert_called_once()
        mock_result.first.assert_called_once()
        self.assertEqual(result, mock_template)

    async def test_get_template_not_found(self):
        """Возврат None, если шаблон не найден"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        self.session.exec.return_value = mock_result

        result = await self.repo.get(self.course_id, self.template_id)

        self.assertIsNone(result)

    async def test_update_template_success(self):
        """Успешное обновление шаблона возвращает True"""
        self.session.execute.return_value.rowcount = 1
        update_data = UpdateTemplate(id=self.template_id, name="Updated Name")

        result = await self.repo.update(self.course_id, update_data)

        self.session.execute.assert_called_once()
        self.assertTrue(result)

    async def test_update_template_no_values(self):
        """Если UpdateTemplate пустой — возврат False и update не вызывается"""
        update_data = UpdateTemplate(id=self.template_id)

        result = await self.repo.update(self.course_id, update_data)

        self.assertFalse(result)
        self.session.execute.assert_not_called()

    async def test_update_template_not_found(self):
        """Если строк не изменилось — возврат False"""
        self.session.execute.return_value.rowcount = 0
        update_data = UpdateTemplate(id=self.template_id, name="Not Found")

        result = await self.repo.update(self.course_id, update_data)

        self.session.execute.assert_called_once()
        self.assertFalse(result)

    async def test_delete_template_success(self):
        """Удаление существующего шаблона возвращает True"""
        self.session.execute.return_value.rowcount = 1

        result = await self.repo.delete(self.course_id, self.template_id)

        self.session.execute.assert_called_once()
        self.assertTrue(result)

    async def test_delete_template_not_found(self):
        """Если шаблон не найден при удалении — возврат False"""
        self.session.execute.return_value.rowcount = 0

        result = await self.repo.delete(self.course_id, self.template_id)

        self.session.execute.assert_called_once()
        self.assertFalse(result)

    async def test_get_all_templates_including_drafts(self):
        """Возвращает все шаблоны пользователя (вместе с черновиками)"""
        mock_templates = [MagicMock(spec=Template), MagicMock(spec=Template)]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_templates
        self.session.exec.return_value = mock_result

        result = await self.repo.get_all_by_course_user(self.course_id, self.user_id, include_drafts=True)

        self.session.exec.assert_called_once()
        mock_result.all.assert_called_once()
        self.assertEqual(result, mock_templates)

    async def test_get_all_templates_without_drafts(self):
        """Возвращает только опубликованные шаблоны"""
        mock_templates = [MagicMock(spec=Template)]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_templates
        self.session.exec.return_value = mock_result

        result = await self.repo.get_all_by_course_user(self.course_id, self.user_id, include_drafts=False)

        self.session.exec.assert_called_once()
        mock_result.all.assert_called_once()
        self.assertEqual(result, mock_templates)


if __name__ == '__main__':
    unittest.main()
