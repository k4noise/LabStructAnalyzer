import uuid
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

    async def create(self, template: Template) -> Template:
        """
        Сохраняет шаблон вместе с элементами в БД.

        Args:
            template: Подготовленный к сохранению шаблон

        Returns:
            Модель шаблона после сохранения с актуальными данными
        """
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def get_by_id(self, template_id: uuid.UUID) -> Optional[Template]:
        """
        Возвращает шаблон по ID.

        Args:
            template_id: ID шаблона (UUIDv4)

        Returns:
            Модель шаблона, если шаблон с переданным id существует, иначе None
        """
        return await self.session.get(Template, template_id)

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


class TemplateElementService:
    """
    Сервис для работы с элементами шаблона (частичный CRUD)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

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

    async def get_elements_with_files(self, template_id: uuid.UUID):
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
