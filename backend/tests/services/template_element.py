import uuid
import unittest
from unittest.mock import MagicMock, AsyncMock

from labstructanalyzer.domain.template_element import PlainTemplateElement, TemplateElementPropsUpdate
from labstructanalyzer.repository.template_element import TemplateElementRepository
from labstructanalyzer.schemas.template_element import TemplateElementProperties, CreateTemplateElementRequest
from labstructanalyzer.services.template_element import TemplateElementService


class TestTemplateElementService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Настраивает мок репозитория и экземпляр сервиса перед каждым тестом"""
        self.mock_repository = AsyncMock(spec=TemplateElementRepository)
        self.service = TemplateElementService(self.mock_repository)
        self.template_id = uuid.uuid4()

    async def test_create_with_nested_structure(self):
        """Проверка корректного создания вложенных элементов"""
        child_dto = CreateTemplateElementRequest(element_type="text_child", properties={"text": "child"},
                                                 id=uuid.uuid4(), data="123")
        parent_dto = CreateTemplateElementRequest(element_type="container", properties={}, data=[child_dto],
                                                  id=uuid.uuid4())

        await self.service.create(self.template_id, [parent_dto])

        self.mock_repository.bulk_create.assert_called_once()

        call_args = self.mock_repository.bulk_create.call_args.args
        actual_template_id = call_args[0]
        actual_flat_list = call_args[1]

        self.assertEqual(actual_template_id, self.template_id)
        self.assertEqual(len(actual_flat_list), 2)  # Родитель + потомок

        parent_element = actual_flat_list[0]
        self.assertIsInstance(parent_element, PlainTemplateElement)
        self.assertEqual(parent_element.element_type, "container")
        self.assertEqual(parent_element.order, 1)
        self.assertIsNone(parent_element.parent_element_id)

        child_element = actual_flat_list[1]
        self.assertEqual(child_element.type, "text_child")
        self.assertEqual(child_element.order, 1)  # Порядок внутри своего родителя
        self.assertEqual(child_element.parent_element_id, parent_element.element_id)

    async def test_create_with_empty_list(self):
        """Создание пустого списка элементов игнорируется"""
        await self.service.create(self.template_id, [])
        self.mock_repository.bulk_create.assert_not_called()

    async def test_update_successful(self):
        """Обновление существующих элементов происходит корректно"""
        update_dto = TemplateElementProperties(id=uuid.uuid4(), properties={"x": 1})
        await self.service.update(self.template_id, [update_dto])

        self.mock_repository.bulk_update_properties.assert_called_once()
        call_args = self.mock_repository.bulk_update_properties.call_args.args

        actual_template_id = call_args[0]
        actual_commands = call_args[1]

        self.assertEqual(actual_template_id, self.template_id)
        self.assertEqual(len(actual_commands), 1)
        self.assertIsInstance(actual_commands[0], TemplateElementPropsUpdate)
        self.assertEqual(actual_commands[0].id, update_dto.id)
        self.assertEqual(actual_commands[0].properties, update_dto.properties)

    async def test_update_with_empty_list(self):
        """Обновление пустого списка элементов игнорируется"""
        await self.service.update(self.template_id, [])

        self.mock_repository.bulk_update_properties.assert_not_called()

    async def test_delete_passes_through_call_and_result(self):
        """Корректное удаление элементов шаблона"""
        ids_to_delete = [uuid.uuid4()]
        self.mock_repository.bulk_delete.return_value = 1

        result = await self.service.delete(self.template_id, ids_to_delete)
        self.mock_repository.bulk_delete.assert_called_once_with(self.template_id, ids_to_delete)
        self.assertEqual(result, 1)

    async def test_get_media_keys_in_elements_extracts_data(self):
        """Извлечение всех ключей к медиа-объектам из элементов шаблона"""
        mock_element_1 = MagicMock()
        mock_element_1.data = "path/to/image1.jpg"
        mock_element_2 = MagicMock()
        mock_element_2.data = "path/to/video.mp4"

        self.mock_repository.get_elements_with_media.return_value = [mock_element_1, mock_element_2]
        result = await self.service.get_media_keys_in_elements(self.template_id)

        self.mock_repository.get_elements_with_media.assert_called_once_with(self.template_id)
        self.assertEqual(result, ["path/to/image1.jpg", "path/to/video.mp4"])

    async def test_get_media_keys_in_elements_when_no_media(self):
        """Пустой список, если не найдено ни одного элемента с медиа-содержимым"""
        self.mock_repository.get_elements_with_media.return_value = []
        result = await self.service.get_media_keys_in_elements(self.template_id)

        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
