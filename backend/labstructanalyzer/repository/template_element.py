import uuid
from collections.abc import Sequence
from dataclasses import asdict
from typing import Any, Dict

from sqlalchemy import Select
from sqlmodel import select, col, insert, delete, update, bindparam
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.domain.template_element import PlainTemplateElement, TemplateElementPropsUpdate
from labstructanalyzer.models.template_element import TemplateElement


class TemplateElementRepository:
    """Управление элементами шаблона"""
    TYPES_WITH_MEDIA = ["image"]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_create(self, template_id: uuid.UUID, components: Sequence[PlainTemplateElement]) -> Sequence[
        uuid.UUID]:
        """
        Сохраняет элементы шаблона

        Args:
            template_id: id шаблона
            components: список элементов шаблона, нормализованных после парсера

        Returns:
            Список идентификаторов элементов шаблона
        """
        if not components:
            return []

        elements_with_template_id = [
            {**asdict(item), "template_id": template_id}
            for item in components
        ]

        await self.session.execute(insert(TemplateElement).values(elements_with_template_id))
        return [item.element_id for item in components]

    async def bulk_update_properties(self, template_id: uuid.UUID,
                                     updates: Sequence[TemplateElementPropsUpdate]) -> int:
        """
        Массово обновляет свойства указанных элементов шаблона

        Args:
            template_id: идентификатор шаблона
            updates: список объектов с ID элемента и словарем обновленных свойств

        Returns:
            Количество обновленных элементов
        """
        if not updates:
            return 0

        patches = {changed_element.element_id: changed_element.properties for changed_element in updates}
        element_ids = list(patches.keys())

        current_properties = await self._fetch_current_properties(template_id, element_ids)
        if not current_properties:
            return 0

        update_payload = self._prepare_update_payload(current_properties, patches)
        if not update_payload:
            return 0

        statement = (
            update(TemplateElement)
            .where(
                col(TemplateElement.id) == bindparam("element_id"),
            )
            .values(properties=bindparam("properties"))
        )
        result = await self.session.execute(statement, update_payload)
        return result.rowcount or 0

    async def bulk_delete(self, template_id: uuid.UUID, ids_to_delete: Sequence[uuid.UUID]) -> int:
        """
        Массово удаляет элементы шаблона

        Args:
           template_id: идентификатор шаблона
           ids_to_delete: список идентификаторов элементов шаблона для последующего удаления

        Returns:
           Количество удаленных элементов
       """
        if not ids_to_delete:
            return 0

        statement = (
            delete(TemplateElement)
            .where(
                col(TemplateElement.id).in_(ids_to_delete),
                col(TemplateElement.template_id) == template_id
            )
        )
        result = await self.session.execute(statement)
        return result.rowcount or 0

    async def get_elements_with_media(self, template_id: uuid.UUID) -> Sequence[TemplateElement]:
        """
        Получает все элементы шаблона, связанные с медиа-файлами

        Args:
            template_id: идентификатор шаблона

        Returns:
            Список моделей элементов шаблона, связанных с медиа-файлами
        """
        statement: Select = select(TemplateElement).where(
            TemplateElement.template_id == template_id,
            col(TemplateElement.type).in_(self.TYPES_WITH_MEDIA)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def _fetch_current_properties(self, template_id: uuid.UUID, element_ids: Sequence[uuid.UUID]) \
            -> Dict[uuid.UUID, Dict[str, Any]]:
        """
        Загружает текущие свойства для указанных element_ids

        Args:
            template_id: идентификатор шаблона
            element_ids: список идентификаторов для поиска

        Returns:
            Словарь, где ключ - идентификатор, а значение - его свойства
        """
        if not element_ids:
            return {}

        statement: Select = (
            select(TemplateElement.id, TemplateElement.properties)
            .where(
                TemplateElement.template_id == template_id,
                col(TemplateElement.id).in_(element_ids),
            )
            .with_for_update()
        )
        rows = (await self.session.exec(statement)).all()
        return {row.element_id: row.properties for row in rows}

    def _prepare_update_payload(
            self,
            current_properties: Dict[uuid.UUID, Dict],
            updates: Dict[uuid.UUID, Dict],
    ) -> Sequence[Dict[str, Any]]:
        """
        Выполняет слияние старых свойств элемента с новыми

        Args:
            current_properties: текущие свойства элементов в виде словаря
            updates: словарь изменений

        Returns:
            Список данных элементов с обновленными свойствами
        """
        merged_rows = []
        for element_id, old_props in current_properties.items():
            if element_id in updates:
                new_props = old_props.copy() | updates[element_id]
                if new_props == old_props:
                    continue
                merged_rows.append({
                    "element_id": element_id,
                    "properties": new_props
                })
        return merged_rows
