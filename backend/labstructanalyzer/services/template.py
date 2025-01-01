import uuid
from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlparse

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from labstructanalyzer.core.exceptions import TemplateNotFoundException
from labstructanalyzer.models.dto.template_element import TemplateElementDto
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

    async def update(self, data_to_modify: TemplateToModify):
        """
        Обновляет данные сохраненного шаблона - изменяет только те параметры, которые были переданы пользователем.

        Args:
            data_to_modify: Новые данные шаблона

        Raises:
            TemplateNotFoundError: Шаблон не найден
        """
        template = self.get_by_id(data_to_modify.template_id)
        if template is None:
            raise TemplateNotFoundException(data_to_modify.template_id)

        if data_to_modify.name is not None:
            template.name = data_to_modify.name

        if data_to_modify.max_score is not None:
            template.max_score = data_to_modify.max_score

        template.is_draft = data_to_modify.is_draft

        if data_to_modify.updated_elements:
            await self.elements_service.bulk_update_properties(data_to_modify.updated_elements)

        if data_to_modify.deleted_elements:
            await self.elements_service.bulk_delete_elements(data_to_modify.deleted_elements)

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

        self.elements_service.remove_files_by_elements(template.template_id)
        await self.session.delete(template)
        await self.session.commit()

    async def get_all_by_course(self, course_id: str) -> List[Template]:
        """
        Возвращает шаблоны по course_id, которые не являются черновиками.
        Может вернуть пустой лист
        """
        statement = select(Template).where(
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

    async def bulk_update_properties(self, elements_to_update: list[TemplateElementDto]):
        """
        Массово обновляет элементы, производя частичную замену свойств

        Args:
            elements_to_update: Данные элементов с обновленными свойствами
        """
        for updated_element in elements_to_update:
            template_element = await self.session.get(TemplateElement, updated_element.element_id)
            if template_element:
                template_element.properties.update(updated_element.properties)

    async def bulk_delete_elements(self, elements_to_remove: list[TemplateElementDto]):
        """
        Массово удаляет элементы

        Args:
            elements_to_remove: Элементы к удалению
        """
        for updated_element in elements_to_remove:
            template_element = await self.session.get(TemplateElement, updated_element.element_id)
            if template_element:
                await self.session.delete(template_element)

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
