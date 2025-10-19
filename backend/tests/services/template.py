import unittest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

from labstructanalyzer.exceptions.access_denied import InvalidCourseAccessDeniedException
from labstructanalyzer.exceptions.invalid_action import InvalidTransitionException
from labstructanalyzer.exceptions.no_entity import TemplateNotFoundException
from labstructanalyzer.models.template import Template
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.schemas.template import TemplateUpdateRequest, TemplateCreationResponse, \
    TemplateDetailResponse
from labstructanalyzer.schemas.template_element import TemplateElementUpdateRequest, TemplateElementUpdateAction
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
        """Создание шаблона: repo.create вызывает генерацию id, сервис возвращает DTO и логирует его"""
        fake_template = Template(
            id=uuid.uuid4(),
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

        self.assertIsInstance(result, TemplateCreationResponse)
        self.assertEqual(result.id, fake_template.id)

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
        self.assertIsInstance(dto, TemplateDetailResponse)
        self.assertEqual(dto.id, self.template_id)

    async def test_get_not_found(self):
        """Попытка получения несуществующего шаблона вызывает TemplateNotFoundException"""
        self.repo.get.return_value = None
        with self.assertRaises(TemplateNotFoundException):
            await self.service.get(self.user, self.template_id)
        self.mock_logger_instance.info.assert_not_called()

    async def test_update_success(self):
        """Успешное обновление существующего шаблона и его элементов"""
        self.repo.get.return_value = Template(
            id=self.template_id, course_id="c1", user_id="u1", name="Test", is_draft=False
        )

        element_to_delete = TemplateElementUpdateRequest(action=TemplateElementUpdateAction.DELETE,
                                                         id=uuid.uuid4())
        element_to_create = TemplateElementUpdateRequest(action=TemplateElementUpdateAction.CREATE, type="text",
                                                         id=uuid.uuid4())
        element_to_update = TemplateElementUpdateRequest(action=TemplateElementUpdateAction.UPDATE,
                                                         id=uuid.uuid4(), properties={"a": 1})

        mod = TemplateUpdateRequest(
            name="New",
            max_score=10,
            elements=[element_to_delete, element_to_create, element_to_update],
            id=self.template_id,
            is_draft=True
        )

        await self.service.update(self.user, self.template_id, mod)

        self.repo.update.assert_awaited()
        self.elem_service.delete.assert_awaited_with(self.template_id, [element_to_delete])
        self.elem_service.create.assert_awaited_with(self.template_id, [element_to_create])
        self.elem_service.update.assert_awaited_with(self.template_id, [element_to_update])
        self.mock_logger_instance.info.assert_called_with(f"Шаблон обновлен: id {self.template_id}")

    async def test_publish_success(self):
        """Успешная публикация шаблона"""
        self.repo.get.return_value = Template(id=self.template_id, course_id="c1", user_id="u1", name="Test",
                                              is_draft=True)

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
        mod = TemplateUpdateRequest(name="Test", elements=[], id=self.template_id, is_draft=True)
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

    async def test_get_all_by_course_user_student_role(self):
        """Проверяем, что для студента в DTO передается пользователь без ролей"""
        student = User(sub="s1", course_id="c1", roles=[], launch_id="x")
        t1 = Template(id=self.template_id, user_id="u1", course_id="c1", name="T", is_draft=False)
        t1.reports = []
        self.repo.get_all_by_course_user.return_value = [t1]
        self.course.name = "Course"

        result = await self.service.get_all_by_course_user(student, self.course)

        self.assertEqual(result.user.sub, "s1")
        self.assertEqual(result.user.roles, [])

    async def test_get_all_by_course_user_assistant_role(self):
        """Проверяем, что для ассистента в DTO передается пользователь с ролью ASSISTANT"""
        assistant = User(sub="a1", course_id="c1", roles=[UserRole.ASSISTANT], launch_id="x")
        t1 = Template(id=self.template_id, user_id="u1", course_id="c1", name="T", is_draft=False)
        t1.reports = []
        self.repo.get_all_by_course_user.return_value = [t1]
        self.course.name = "Course"

        result = await self.service.get_all_by_course_user(assistant, self.course)

        self.assertEqual(result.user.sub, "a1")
        self.assertIn(UserRole.ASSISTANT, result.user.roles)

    async def test_modify_elements_empty(self):
        """_modify_elements с пустым списком вызывает сервисы с пустыми списками"""
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


if __name__ == '__main__':
    unittest.main()
