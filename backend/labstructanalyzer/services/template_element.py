import uuid
from typing import Sequence, Optional, Dict, Any

from labstructanalyzer.domain.template_element import PlainTemplateElement, TemplateElementPropsUpdate
from labstructanalyzer.repository.template_element import TemplateElementRepository
from labstructanalyzer.schemas.template_element import (
    CreateTemplateElementRequest,
    TemplateElementProperties,
)


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
                element_id=item.id,
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
        return [element.properties.get("data") for element in elements_with_media]

    def _prepare_data_recursive(
            self,
            components: Sequence[CreateTemplateElementRequest],
            parent_id: Optional[uuid.UUID] = None
    ) -> Sequence[PlainTemplateElement]:
        """Рекурсивно преобразует компоненты, объединяя properties и data"""
        prepared_list: list[PlainTemplateElement] = []

        for i, component in enumerate(components, 1):
            children: Optional[Sequence[CreateTemplateElementRequest]] = None
            merged_props = (component.properties or {}).copy()

            if isinstance(component.data, list):
                children = component.data
            elif component.data is not None:
                merged_props['data'] = component.data

            current = PlainTemplateElement(
                type=component.type,
                properties=merged_props,
                order=i,
                parent_element_id=parent_id
            )
            prepared_list.append(current)

            if children is not None:
                prepared_list.extend(
                    self._prepare_data_recursive(children, parent_id=current.id)
                )

        return prepared_list
