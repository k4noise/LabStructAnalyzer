import copy
import uuid
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy import func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, and_, desc

from labstructanalyzer.core.exceptions import TemplateNotFoundException
from labstructanalyzer.models.dto.template_element import TemplateElementDto, BaseTemplateElementDto
from labstructanalyzer.models.report import Report
from labstructanalyzer.models.template import Template
from labstructanalyzer.models.template_element import TemplateElement
from labstructanalyzer.models.dto.modify_template import TemplateToModify
from labstructanalyzer.services.report import ReportStatus
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

    async def get_by_id(self, template_id: uuid.UUID) -> Optional[Template]:
        """
        Возвращает шаблон по ID.

        Args:
            template_id: ID шаблона (UUIDv4)

        Returns:
            Модель шаблона, если шаблон с переданным id существует, иначе None
        """
        return await self.session.get(Template, template_id)

    async def update(self, template_id: uuid.UUID, data_to_modify: TemplateToModify):
        """
        Обновляет данные сохраненного шаблона - изменяет только те параметры, которые были переданы пользователем.
        Для опубликованного шаблона нельзя изменять имя и максимальный балл

        Args:
            template_id: id шаблона
            data_to_modify: Новые данные шаблона

        Raises:
            TemplateNotFoundError: Шаблон не найден
        """
        template = await self.get_by_id(template_id)
        if template is None:
            raise TemplateNotFoundException(template_id)

        if template.is_draft:
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

    async def get_all_by_course(
            self,
            course_id: str,
            user_id: str,
            is_draft: bool = False,
            with_reports: bool = False
    ):
        """
        Возвращает id и имена всех шаблонов по course_id, которые не являются черновиками.
        Если with_reports=True, то также возвращает информацию об отчетах.
        Может вернуть пустой список.
        """
        if with_reports:
            report_subquery = (
                select(
                    Report.template_id,
                    Report.author_id,
                    Report.report_id,
                    Report.status,
                    func.max(Report.created_at).label("latest_created_at")
                )
                .where(Report.author_id == user_id)
                .group_by(Report.template_id, Report.author_id, Report.report_id, Report.status)
                .subquery()
            )

            statement = (
                select(
                    Template.template_id,
                    Template.name,
                    report_subquery.c.report_id,
                    report_subquery.c.status
                )
                .select_from(Template)
                .outerjoin(
                    report_subquery,
                    Template.template_id == report_subquery.c.template_id
                )
                .where(
                    Template.course_id == course_id,
                    Template.is_draft == is_draft
                )
            )
        else:
            statement = (
                select(
                    Template.template_id,
                    Template.name
                )
                .where(
                    Template.course_id == course_id,
                    Template.is_draft == is_draft
                )
            )

        result = await self.session.exec(statement)
        return result.all()

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

    async def get_all_reports(self, template_id: uuid.UUID) -> list[Report]:
        """
        Получить все доступные отчеты - проверенные ранее или ожидающие проверки
        """
        statement = select(Report).where(
            Report.template_id == template_id,
            Report.status != ReportStatus.saved.name
        ).order_by(desc(Report.created_at))

        return (await self.session.exec(statement)).unique().all()

    async def get_by_report_id(self, report_id: uuid.UUID):
        """
        Получить объект шаблона по id отчета
        """
        report = await self.session.get(Report, report_id)
        return report.template

    async def get_all_answer_elements_id(self, report_id: uuid.UUID):
        template = self.get_by_report_id(report_id)
        return self.elements_service.get_all_answer_elements_id(template.id)


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

    async def get_all_answer_elements_id(self, template_id: uuid.UUID):
        """
        Получает id всех элементов ответов
        """
        elements_query = select(TemplateElement.element_id).where(
            TemplateElement.template_id == template_id,
            TemplateElement.element_type == 'answer'
        )
        return await self.session.exec(elements_query).all()
