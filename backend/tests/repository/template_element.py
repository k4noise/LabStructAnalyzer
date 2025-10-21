import uuid
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from labstructanalyzer.domain.template_element import TemplateElementPropsUpdate, PlainTemplateElement
from labstructanalyzer.repository.template_element import TemplateElementRepository


class TestTemplateElementRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Настраивает тестовое окружение перед каждым тестом -
        создает мок асинхронной сессии и экземпляр репозитория
        """
        self.session = MagicMock()
        self.session.exec = AsyncMock()
        self.session.execute = AsyncMock()

        self.repository = TemplateElementRepository(self.session)
        self.template_id = uuid.uuid4()

    def _create_mock_element(self, element_id, props):
        """Создает мок-объект элемента, имитирующий строку из базы данных"""
        mock_row = MagicMock()
        mock_row.element_id = element_id
        mock_row.properties = props
        return mock_row

    def _setup_session_exec_result(self, elements: list):
        """
        Настраивает мок session.exec для возврата указанного списка элементов,
        необходим для корректной имитации цепочки вызовов
        `(await session.exec(...)).all()`
        """
        mock_result_object = MagicMock()
        mock_result_object.all.return_value = elements
        self.session.exec.return_value = mock_result_object

    async def test_bulk_update_properties_no_changes_after_merge(self):
        """Запрос на обновление свойств не должен уходить в БД, если свойства не изменились"""
        element_id = uuid.uuid4()
        patch_data = TemplateElementPropsUpdate(element_id=element_id, properties={"x": 1})
        mock_element = self._create_mock_element(element_id, props={"x": 1})
        self._setup_session_exec_result([mock_element])

        result = await self.repository.bulk_update_properties(self.template_id, [patch_data])

        self.assertEqual(result, 0)
        self.session.exec.assert_called_once()
        self.session.execute.assert_not_called()

    async def test_bulk_update_properties_successful_merge(self):
        """Запрос на обновление свойств должен корректно перезаписывать старые свойства новыми"""
        element_id = uuid.uuid4()
        patch_data = TemplateElementPropsUpdate(element_id=element_id, properties={"y": 100, "z": 99})
        expected_props = {"x": 1, "y": 100, "z": 99}
        mock_element = self._create_mock_element(element_id, props={"x": 1, "y": 2})
        self._setup_session_exec_result([mock_element])
        self.session.execute.return_value.rowcount = 1

        result = await self.repository.bulk_update_properties(self.template_id, [patch_data])

        self.assertEqual(result, 1)
        self.session.exec.assert_called_once()
        self.session.execute.assert_called_once()

        payload = self.session.execute.call_args[0][1]
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['properties'], expected_props)

    async def test_bulk_update_properties_non_existent_element(self):
        """Обновление элементов вне необходимого шаблона и/или несуществующего в целом игнорируется"""
        patch_data = TemplateElementPropsUpdate(element_id=uuid.uuid4(), properties={"x": 1})
        self._setup_session_exec_result([])

        result = await self.repository.bulk_update_properties(self.template_id, [patch_data])

        self.assertEqual(result, 0)
        self.session.exec.assert_called_once()
        self.session.execute.assert_not_called()

    async def test_bulk_update_properties_empty_list(self):
        """Обновление элементов по пустому списку пропускается"""
        result = await self.repository.bulk_update_properties(self.template_id, [])

        self.assertEqual(result, 0)
        self.session.exec.assert_not_called()
        self.session.execute.assert_not_called()

    async def test_bulk_create_successful(self):
        """Корректное создание элементов, возвращение идентификаторов"""
        components = [PlainTemplateElement(element_type='test', order=0),
                      PlainTemplateElement(element_type="image", order=1)]
        expected_ids = [component.element_id for component in components]

        result = await self.repository.bulk_create(self.template_id, components)

        self.assertEqual(result, expected_ids)
        self.session.execute.assert_called_once()

    async def test_bulk_create_empty_list(self):
        """Создание элементов по пустому списку пропускается"""
        result = await self.repository.bulk_create(self.template_id, [])

        self.assertEqual(result, [])
        self.session.execute.assert_not_called()

    async def test_bulk_delete_successful(self):
        """Корректное удаление элементов и возврат количества удаленных"""
        ids_to_delete = [uuid.uuid4(), uuid.uuid4()]
        self.session.execute.return_value.rowcount = 2

        result = await self.repository.bulk_delete(self.template_id, ids_to_delete)

        self.assertEqual(result, 2)
        self.session.execute.assert_called_once()

    async def test_bulk_delete_wrong_template_id_for_security(self):
        """Элемент из чужого шаблона будет проигнорирован"""
        ids_to_delete = [uuid.uuid4()]
        self.session.execute.return_value.rowcount = 0

        result = await self.repository.bulk_delete(uuid.uuid4(), ids_to_delete)

        self.assertEqual(result, 0)
        self.session.execute.assert_called_once()

    async def test_bulk_delete_empty_list(self):
        """Удаление пустого списка элементов игнорируется"""
        result = await self.repository.bulk_delete(self.template_id, [])

        self.assertEqual(result, 0)
        self.session.execute.assert_not_called()

    async def test_get_elements_with_media_returns_only_media_types(self):
        """Успешный возврат элементов только с медиа"""
        media_element = self._create_mock_element(uuid.uuid4(), props={})
        media_element.element_type = 'image'
        self._setup_session_exec_result([media_element])

        with patch.object(self.repository, 'TYPES_WITH_MEDIA', ['image', 'video']):
            result = await self.repository.get_elements_with_media(self.template_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, 'image')
        self.session.exec.assert_called_once()

    async def test_get_elements_with_media_returns_empty_list(self):
        """Возврат пустого списка, если элементы с медиа отсутствуют в шаблоне"""
        self._setup_session_exec_result([])

        result = await self.repository.get_elements_with_media(self.template_id)

        self.assertEqual(result, [])
        self.session.exec.assert_called_once()


if __name__ == '__main__':
    unittest.main()
