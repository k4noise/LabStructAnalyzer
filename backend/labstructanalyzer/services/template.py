import copy
import uuid
from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlparse

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from labstructanalyzer.core.exceptions import TemplateNotFoundException
from labstructanalyzer.models.dto.template_element import TemplateElementDto, BaseTemplateElementDto
from labstructanalyzer.models.template import Template
from labstructanalyzer.models.template_element import TemplateElement
from labstructanalyzer.models.dto.modify_template import TemplateToModify
from labstructanalyzer.utils.file_utils import FileUtils


class TemplateService:
    """
    Сервис для работы с шаблонами отчетов (CRUD операции)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.elements_service = TemplateElementService(session)

    async def create(self, author_id: str, course_id: str, name: str, template_components: list[dict]) -> Template:
        """
        Сохраняет шаблон вместе с элементами в БД.

        Args:
            author_id: id пользователя, создающего шаблон
            course_id: id курса, для которого создается шаблон
            name: Имя шаблона
            template_components: Массив преобразованных парсером элементов с примененной структурой

        Returns:
            Модель шаблона после сохранения с актуальными данными
        """
        template = Template(
            user_id=author_id,
            course_id=course_id,
            name=name,
            is_draft=True,
            elements=self.elements_service.bulk_create_elements(template_components, None)
        )
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    @lru_cache
    async def get_by_id(self, template_id: uuid.UUID) -> Optional[Template]:
        """
        Возвращает шаблон по ID.

        Args:
            template_id: ID шаблона (UUIDv4)

        Returns:
            Модель шаблона, если шаблон с переданным id существует, иначе None
        """
        template = await self.session.get(Template, template_id)
        return template

    async def update(self, template_id: uuid.UUID, data_to_modify: TemplateToModify):
        """
        Обновляет данные сохраненного шаблона - изменяет только те параметры, которые были переданы пользователем.

        Args:
            template_id: id шаблона
            data_to_modify: Новые данные шаблона

        Raises:
            TemplateNotFoundError: Шаблон не найден
        """
        template = await self.get_by_id(template_id)
        if template is None:
            raise TemplateNotFoundException(template_id)

        template.name = data_to_modify.name
        template.max_score = data_to_modify.max_score
        template.is_draft = data_to_modify.is_draft

        if data_to_modify.updated_elements:
            await self.elements_service.bulk_update_properties(template_id, data_to_modify.updated_elements)

        if data_to_modify.deleted_elements:
            await self.elements_service.bulk_delete_elements(template_id, data_to_modify.deleted_elements)

        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def delete(self, template_id: uuid.UUID) -> None:
        """
        Удаляет шаблон и все его элементы каскадно из БД, также удаляет сохраненные файлы

        Raises:
            TemplateNotFoundError: Шаблон не найден
        """
        template = await self.session.get(Template, template_id)
        if template is None:
            raise TemplateNotFoundException(template_id)

        await self.elements_service.remove_all_files_from_data(template.template_id)
        await self.session.delete(template)
        await self.session.commit()

    async def get_all_by_course(self, course_id: str):
        """
        Возвращает id и имена всех шаблонов по course_id, которые не являются черновиками.
        Может вернуть пустой лист
        """
        statement = select(Template.template_id, Template.name).where(
            Template.course_id == course_id,
            Template.is_draft == False
        )
        result = await self.session.exec(statement)
        return result.unique().all()

    def build_hierarchy(self, elements: list[TemplateElement]):
        """
        Строит иерархическую структуру элементов из плоского списка.

        Args:
            elements (list[TemplateElement]): Список элементов.

        Returns:
            list[dict]: Иерархическая структура элементов.
        """
        def build_subtree(parent_id):
            subtree = []
            for element in elements:
                if element.parent_element_id == parent_id:
                    data = build_subtree(element.element_id)
                    properties = element.properties.copy()
                    if data:
                        properties["data"] = data
                    subtree.append({
                        "element_type": element.element_type,
                        "element_id": element.element_id,
                        "properties": properties
                    })
            return subtree

        return build_subtree(None)

class TemplateElementService:
    """
    Сервис для работы с элементами шаблона (частичный CRUD)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def bulk_create_elements(self, components: list[dict], parent_id=None):
        """
        Массово создает модели элементов из списка структурных компонент парсера, в том числе обрабатывает вложенные элементы.
        Модели создаются без template_id для одновременного сохранения внутри модели Template

        Args:
            components: Список структурных компонент
            parent_id: id родительского элемента, для элементов первого уровня вложенности должен быть None

        Returns:
            Массив моделей элементов
        """

        elements = []
        i = 1
        for component in components:
            if isinstance(component, list):
                child_elements = self.bulk_create_elements(
                    component,
                    parent_id
                )
                elements.extend(child_elements)
                continue

            data = None
            if "data" in component and isinstance(component["data"], list):
                data = component["data"]
                del component["data"]

            element = TemplateElement(
                properties=component,
                element_type=component.get("type"),
                order=i,
                parent_element_id=parent_id
            )
            elements.append(element)
            i += 1

            if data:
                child_elements = self.bulk_create_elements(
                    data,
                    element.element_id
                )
                elements.extend(child_elements)
        return elements

    async def bulk_update_properties(self, template_id: uuid.UUID, elements_to_update: list[BaseTemplateElementDto]):
        """
        Массово обновляет элементы, относящиеся к определенному шаблону, производя частичную замену свойств.
        Элементы из другого шаблона или несуществующие будут проигнорированы.

        Args:
            template_id: id шаблона
            elements_to_update: Данные элементов с обновленными свойствами
        """
        for updated_element in elements_to_update:
            template_element = await self.session.get(TemplateElement, updated_element.element_id)
            if template_element and template_element.template_id == template_id:
                properties = copy.deepcopy(template_element.properties)
                properties.update(updated_element.properties)
                template_element.properties = properties

        await self.session.commit()

    async def bulk_delete_elements(self, template_id: uuid.UUID, elements_to_remove: list[TemplateElementDto]):
        """
        Массово удаляет элементы, относящиеся к определенному шаблону.
        Элементы из другого шаблона или несуществующие будут проигнорированы.

        Args:
            template_id: id шаблона
            elements_to_remove: Элементы к удалению
        """
        for updated_element in elements_to_remove:
            template_element = await self.session.get(TemplateElement, updated_element.element_id)
            if template_element and template_element.template_id == template_id:
                await self.session.delete(template_element)

        await self.session.commit()

    async def remove_all_files_from_data(self, template_id: uuid.UUID):
        """
        Для всех элементов шаблона находит те, которые имеют сохраненные файлы на диске и удаляет их
        """
        image_elements: list[TemplateElement] = await self.session.exec(
            select(TemplateElement).where(
                TemplateElement.template_id == template_id,
                TemplateElement.element_type == "image"
            )
        )
        if image_elements is not None:
            for image_element in image_elements:
                image_path = image_element.properties.get("data")
                try:
                    FileUtils.remove("", urlparse(image_path).path)
                finally:
                    continue
