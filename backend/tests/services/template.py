import unittest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

from labstructanalyzer.exceptions.access_denied import InvalidCourseAccessDeniedException
from labstructanalyzer.exceptions.invalid_action import InvalidTransitionException
from labstructanalyzer.exceptions.no_entity import TemplateNotFoundException
from labstructanalyzer.models.template import Template
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.schemas.template import (
    TemplateElementUpdateUnit,
    TemplateElementUpdateAction, TemplateToModify
)
from labstructanalyzer.services.template import TemplateService


class TestTemplateService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Создание мок‑репозиториев, сервисов и глобального логгера"""
        self.repo = MagicMock()
        self.repo.create = AsyncMock()
        self.repo.update = AsyncMock()
        self.repo.delete = AsyncMock()
        self.repo.get = AsyncMock()
        self.repo.get_all_by_course_user = AsyncMock()

        self.elem_service = MagicMock()
        self.elem_service.create = AsyncMock()
        self.elem_service.update = AsyncMock()
        self.elem_service.delete = AsyncMock()
        self.elem_service.get_media_keys_in_elements = AsyncMock()

        self.ags = MagicMock()
        self.files = MagicMock()
        self.course = MagicMock()

        self.mock_logger_instance = MagicMock()
        mock_global_logger = MagicMock()
        mock_global_logger.return_value.get_logger.return_value = self.mock_logger_instance
        patcher = patch('labstructanalyzer.services.template.GlobalLogger', mock_global_logger)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.service = TemplateService(self.repo, self.elem_service)

        self.user = User(sub="u1", course_id="c1", roles=[UserRole.TEACHER], launch_id="launch_id")
        self.template_id = uuid.uuid4()

    async def test_create_success(self):
        """Создание шаблона: repo.create вызывает генерацию id, сервис возвращает и логирует его"""
        fake_template = Template(
            user_id="u1",
            course_id="c1",
            name="Test name",
            is_draft=True
        )
        self.repo.create.return_value = fake_template

        result = await self.service.create(
            self.user,
            "Name",
            [{"element_type": "text", "order": 1, "data": []}]
        )

        self.assertEqual(result, fake_template.id)

        self.elem_service.create.assert_awaited_once_with(
            fake_template.id, unittest.mock.ANY
        )

        self.mock_logger_instance.info.assert_called_with(
            f"Сохранен черновик шаблона: id {fake_template.id}"
        )

    async def test_get_success(self):
        """Успешное получение DTO шаблона"""
        template = Template(id=self.template_id, course_id="c1", user_id="u1", name="Test")
        template.elements = []
        self.repo.get.return_value = template

        dto = await self.service.get(self.user, self.template_id)

        self.repo.get.assert_awaited()
        self.assertEqual(dto.template_id, self.template_id)

    async def test_get_not_found(self):
        """Попытка получения несуществующего шаблона вызывает TemplateNotFoundException"""
        self.repo.get.return_value = None
        with self.assertRaises(TemplateNotFoundException):
            await self.service.get(self.user, self.template_id)

    async def test_update_success(self):
        """Успешное обновление существующего шаблона и его элементов"""
        self.repo.get.return_value = Template(
            id=self.template_id, course_id="c1", user_id="u1", name="Test", is_draft=False
        )
        mod = TemplateToModify(name="New", max_score=10, elements=[], template_id=self.template_id, is_draft=True)

        await self.service.update(self.user, self.template_id, mod)

        self.repo.update.assert_awaited()
        self.elem_service.delete.assert_awaited()
        self.elem_service.create.assert_awaited()
        self.elem_service.update.assert_awaited()
        self.mock_logger_instance.info.assert_called_with(f"Шаблон обновлен: id {self.template_id}")

    async def test_publish_success(self):
        """Успешная публикация шаблона"""
        self.repo.get.return_value = Template(id=self.template_id, course_id="c1", user_id="u1", name="Test",
                                              is_draft=True)
        self.repo.update.return_value = True

        await self.service.publish(self.user, self.template_id, self.ags)

        self.repo.update.assert_awaited()
        self.ags.find_or_create_lineitem.assert_called_once()
        self.mock_logger_instance.info.assert_called_with(f"Шаблон опубликован: id {self.template_id}")

    async def test_publish_invalid_transition(self):
        """Публикация при is_draft=False вызывает InvalidTransitionException"""
        self.repo.get.return_value = Template(id=self.template_id, course_id="c1", user_id="u1", name="Test",
                                              is_draft=False)
        with self.assertRaises(InvalidTransitionException):
            await self.service.publish(self.user, self.template_id, self.ags)

    async def test_delete_success(self):
        """Успешное удаление шаблона: удаляются lineitem и медиафайлы"""
        self.repo.get.return_value = Template(id=self.template_id, course_id="c1", user_id="u1", name="Test")
        self.elem_service.get_media_keys_in_elements.return_value = ["m1", "m2"]

        await self.service.delete(self.user, self.template_id, self.files, self.ags)

        self.repo.delete.assert_awaited()
        self.ags.delete_lineitem.assert_called_once()
        self.files.remove.assert_any_call("m1")
        self.files.remove.assert_any_call("m2")
        self.mock_logger_instance.info.assert_called_with(f"Шаблон удален: id {self.template_id}")

    async def test_get_all_by_course_user(self):
        """Возвращает список DTO шаблонов пользователя в рамках курса"""
        t1 = Template(id=self.template_id, user_id="u1", course_id="c1", name="T", is_draft=False)
        t1.reports = []
        self.repo.get_all_by_course_user.return_value = [t1]
        self.course.name = "Course"

        result = await self.service.get_all_by_course_user(self.user, self.course)

        self.repo.get_all_by_course_user.assert_awaited()
        self.assertEqual(result.course_name, "Course")
        self.assertEqual(result.templates[0].name, "T")

    async def test_update_invalid_course_access(self):
        """Update при другом course_id вызывает InvalidCourseAccessDeniedException"""
        self.repo.get.return_value = Template(id=self.template_id, course_id="x", user_id="u1")
        mod = TemplateToModify(name="Test", elements=[], template_id=self.template_id, is_draft=True)
        with self.assertRaises(InvalidCourseAccessDeniedException):
            await self.service.update(self.user, self.template_id, mod)
        self.mock_logger_instance.info.assert_not_called()

    async def test_publish_invalid_course_access(self):
        """Publish при другом course_id вызывает InvalidCourseAccessDeniedException"""
        self.repo.get.return_value = Template(id=self.template_id, course_id="x", user_id="u1", is_draft=True)
        with self.assertRaises(InvalidCourseAccessDeniedException):
            await self.service.publish(self.user, self.template_id, self.ags)
        self.ags.find_or_create_lineitem.assert_not_called()

    async def test_delete_invalid_course_access(self):
        """Delete при другом course_id вызывает InvalidCourseAccessDeniedException"""
        self.repo.get.return_value = Template(id=self.template_id, course_id="x", user_id="u1")
        with self.assertRaises(InvalidCourseAccessDeniedException):
            await self.service.delete(self.user, self.template_id, self.files, self.ags)
        self.mock_logger_instance.info.assert_not_called()

    async def test_publish_update_failed(self):
        """Если repo.update возвращает False — lineitem не создаётся"""
        self.repo.get.return_value = Template(id=self.template_id, course_id="c1", user_id="u1", is_draft=True)
        self.repo.update.return_value = False

        await self.service.publish(self.user, self.template_id, self.ags)

        self.ags.find_or_create_lineitem.assert_not_called()

        async def test_update_not_found(self):
            """Если repo.update вернул False — выбрасывается TemplateNotFoundException"""

        # мок возврата шаблона, чтобы пройти get()
        self.repo.get.return_value = Template(
            id=self.template_id, course_id="c1", user_id="u1", name="Old", is_draft=False
        )
        # repo.update ничего не обновил
        self.repo.update.return_value = False
        mod = TemplateToModify(name="New", elements=[], template_id=self.template_id, is_draft=True)

        with self.assertRaises(TemplateNotFoundException):
            await self.service.update(self.user, self.template_id, mod)

        self.mock_logger_instance.info.assert_not_called()

    async def test_publish_not_found(self):
        """Если repo.update вернул False при publish — выбрасывается TemplateNotFoundException"""
        self.repo.get.return_value = Template(
            id=self.template_id, course_id="c1", user_id="u1", is_draft=True
        )
        self.repo.update.return_value = False

        with self.assertRaises(TemplateNotFoundException):
            await self.service.publish(self.user, self.template_id, self.ags)

        self.mock_logger_instance.info.assert_not_called()
        self.ags.find_or_create_lineitem.assert_not_called()

    async def test_delete_not_found(self):
        """Если repo.delete вернул False — выбрасывается TemplateNotFoundException"""
        self.repo.get.return_value = Template(
            id=self.template_id, course_id="c1", user_id="u1", name="ToDelete"
        )
        # repo.delete ничего не удалил
        self.repo.delete.return_value = False

        with self.assertRaises(TemplateNotFoundException):
            await self.service.delete(self.user, self.template_id, self.files, self.ags)

        self.mock_logger_instance.info.assert_not_called()
        self.ags.delete_lineitem.assert_not_called()

    async def test_update_not_found(self):
        """Если repo.update вернул False — выбрасывается TemplateNotFoundException"""
        # мок возврата шаблона, чтобы пройти get()
        self.repo.get.return_value = Template(
            id=self.template_id, course_id="c1", user_id="u1", name="Old", is_draft=False
        )
        # repo.update ничего не обновил
        self.repo.update.return_value = False
        mod = TemplateToModify(name="New", elements=[], template_id=self.template_id, is_draft=True)

        with self.assertRaises(TemplateNotFoundException):
            await self.service.update(self.user, self.template_id, mod)

        self.mock_logger_instance.info.assert_not_called()

    async def test_publish_not_found(self):
        """Если repo.update вернул False при publish — выбрасывается TemplateNotFoundException"""
        self.repo.get.return_value = Template(
            id=self.template_id, course_id="c1", user_id="u1", is_draft=True
        )
        self.repo.update.return_value = False

        with self.assertRaises(TemplateNotFoundException):
            await self.service.publish(self.user, self.template_id, self.ags)

        self.mock_logger_instance.info.assert_not_called()
        self.ags.find_or_create_lineitem.assert_not_called()

    async def test_delete_not_found(self):
        """Если repo.delete вернул False — выбрасывается TemplateNotFoundException"""
        self.repo.get.return_value = Template(
            id=self.template_id, course_id="c1", user_id="u1", name="ToDelete"
        )
        # repo.delete ничего не удалил
        self.repo.delete.return_value = False

        with self.assertRaises(TemplateNotFoundException):
            await self.service.delete(self.user, self.template_id, self.files, self.ags)

        self.mock_logger_instance.info.assert_not_called()
        self.ags.delete_lineitem.assert_not_called()

    async def test_get_all_by_course_user_student_role(self):
        """Студент не может upload/grade"""
        student = User(sub="s1", course_id="c1", roles=[], launch_id="x")
        t1 = Template(id=self.template_id, user_id="u1", course_id="c1", name="T", is_draft=False)
        t1.reports = []
        self.repo.get_all_by_course_user.return_value = [t1]
        self.course.name = "Course"

        result = await self.service.get_all_by_course_user(student, self.course)
        self.assertFalse(result.can_upload)
        self.assertFalse(result.can_grade)

    async def test_get_all_by_course_user_assistant_role(self):
        """Ассистент может grade, но не upload"""
        assistant = User(sub="a1", course_id="c1", roles=[UserRole.ASSISTANT], launch_id="x")
        t1 = Template(id=self.template_id, user_id="u1", course_id="c1", name="T", is_draft=False)
        t1.reports = []
        self.repo.get_all_by_course_user.return_value = [t1]
        self.course.name = "Course"

        result = await self.service.get_all_by_course_user(assistant, self.course)
        self.assertFalse(result.can_upload)
        self.assertTrue(result.can_grade)

    async def test_modify_elements_buckets(self):
        """_modify_elements вызывает delete/create/update в зависимости от action"""
        modifiers = [
            TemplateElementUpdateUnit(action=TemplateElementUpdateAction.DELETE, element_id=uuid.uuid4()),
            TemplateElementUpdateUnit(action=TemplateElementUpdateAction.CREATE, element_id=uuid.uuid4(),
                                      element_type="text", properties={"lol": 123}),
            TemplateElementUpdateUnit(action=TemplateElementUpdateAction.UPDATE, element_id=uuid.uuid4(),
                                      properties={}),
        ]
        await self.service._modify_elements(self.template_id, modifiers)
        self.elem_service.delete.assert_awaited_once()
        self.elem_service.create.assert_awaited_once()
        self.elem_service.update.assert_awaited_once()

    async def test_modify_elements_empty(self):
        """_modify_elements с пустым списком не вызывает сервисы"""
        await self.service._modify_elements(self.template_id, [])
        self.elem_service.delete.assert_awaited_once_with(self.template_id, [])
        self.elem_service.create.assert_awaited_once_with(self.template_id, [])
        self.elem_service.update.assert_awaited_once_with(self.template_id, [])

    async def test_map_parser_items_nested(self):
        """_map_parser_items правильно обрабатывает вложенные элементы"""
        items = [{
            "element_type": "group",
            "order": 1,
            "data": [
                {"element_type": "text", "order": 2, "data": []}
            ]
        }]
        result = self.service._map_parser_items(items)
        self.assertEqual(result[0].element_type, "group")
        self.assertEqual(result[0].data[0].element_type, "text")

    async def test_get_not_found_no_logger(self):
        """При TemplateNotFoundException logger успеха не вызывается"""
        self.repo.get.return_value = None
        with self.assertRaises(TemplateNotFoundException):
            await self.service.get(self.user, self.template_id)
        self.mock_logger_instance.info.assert_not_called()


if __name__ == '__main__':
    unittest.main()
