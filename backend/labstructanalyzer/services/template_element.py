import uuid
from typing import Sequence, Optional, Callable

from labstructanalyzer.domain.template_element import PlainTemplateElement, TemplateElementPropsUpdate
from labstructanalyzer.models.template_element import TemplateElement
from labstructanalyzer.repository.template_element import TemplateElementRepository
from labstructanalyzer.schemas.template_element import TemplateElementResponse, CreateTemplateElementRequest, \
    TemplateElementProperties


class TemplateElementService:
    def __init__(self, repository: TemplateElementRepository):
        self.repository = repository

    async def create(self, template_id: uuid.UUID, components: Sequence[CreateTemplateElementRequest]):
        """
        Сохраняет элементы шаблона, корректно обрабатывая вложенную структуру компонентов

        Args:
            template_id: id шаблона
            components: список элементов шаблона, включая вложенные дочерние элементы

        Returns:
            Список идентификаторов моделей элементов шаблона
        """
        if not components:
            return []

        prepared_data = self._prepare_data_recursive(components)
        await self.repository.bulk_create(template_id, prepared_data)

    async def update(self, template_id: uuid.UUID, update_pairs: Sequence[TemplateElementProperties]):
        """
        Обновляет свойства элементов шаблона

        Args:
            template_id: id шаблона
            update_pairs: список, содержащий id элемента и новые свойства
        """
        update_commands: Sequence[TemplateElementPropsUpdate] = [
            TemplateElementPropsUpdate(
                element_id=item.element_id,
                properties=item.properties
            ) for item in update_pairs
        ]

        if update_commands:
            await self.repository.bulk_update_properties(template_id, update_commands)

    async def delete(self, template_id: uuid.UUID, ids_to_delete: Sequence[uuid.UUID]):
        """
        Удаляет элементы шаблона

        Args:
            template_id: id шаблона
            ids_to_delete: список, содержащий id элементов к удалению
        """
        return await self.repository.bulk_delete(template_id, ids_to_delete)

    async def get_media_keys_in_elements(self, template_id: uuid.UUID):
        """
        Получает ключи к файлам, на которые ссылаются элементы шаблона
        """
        elements_with_media = await self.repository.get_elements_with_media(template_id)
        return [element.data for element in elements_with_media]

    @staticmethod
    def search_root_parent(id_map: dict[uuid, Optional[TemplateElement]]) -> Callable[[uuid.UUID], uuid.UUID]:
        def find_root(element_id: uuid.UUID) -> uuid.UUID:
            parent = id_map.get(element_id)
            return element_id if parent is None else find_root(parent.id)

        return lambda element_id: find_root(element_id)

    def _prepare_data_recursive(self, components: Sequence[TemplateElementResponse],
                                parent_id: Optional[uuid.UUID] = None) -> Sequence[PlainTemplateElement]:
        """
        Рекурсивно преобразует иерархию компонентов в плоский список элементов шаблона

        Args:
            components: список компонентов для преобразования
            parent_id: идентификатор родительского элемента для вложенных структур

        Returns:
            Плоский список элементов шаблона
        """
        prepared_list = []
        for i, component in enumerate(components, 1):
            current = PlainTemplateElement(
                element_type=component.element_type,
                properties=component.properties,
                order=i,
                parent_element_id=parent_id
            )
            prepared_list.append(current)
            if isinstance(component.data, list):
                prepared_list.extend(
                    self._prepare_data_recursive(component.data, parent_id=current.element_id)
                )
        return prepared_list
