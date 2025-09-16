import uuid
from collections import defaultdict
from collections.abc import Sequence

from labstructanalyzer.core.logger import GlobalLogger
from labstructanalyzer.exceptions.access_denied import InvalidCourseAccessDeniedException
from labstructanalyzer.exceptions.invalid_action import InvalidTransitionException
from labstructanalyzer.exceptions.no_entity import TemplateNotFoundException
from labstructanalyzer.models.template import Template
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.repository.template import TemplateRepository
from labstructanalyzer.schemas.template import TemplateDetailResponse, TemplateCourseCollection, TemplateCourseSummary, \
    MinimalReport, TemplateElementUpdateUnit, TemplateUpdateRequest, TemplateCreationResponse
from labstructanalyzer.schemas.template_element import TemplateElementDto, CreateTemplateElementDto, \
    TemplateElementUpdateAction
from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.course import CourseService
from labstructanalyzer.services.template_element import TemplateElementService
from labstructanalyzer.utils.files.chain_storage import ChainStorage


class TemplateAccessVerifier:
    def __init__(self, template: Template):
        self.template = template

    def is_valid_course(self, user: User):
        if self.template.course_id != user.course_id:
            raise InvalidCourseAccessDeniedException()
        return self

    def can_publish(self):
        if not self.template.is_draft:
            raise InvalidTransitionException()
        return self


class TemplateService:
    def __init__(self, repository: TemplateRepository, elements_service: TemplateElementService):
        self.repository = repository
        self.elements_service = elements_service
        self.logger = GlobalLogger().get_logger(__name__)

    async def create(self, user: User, name: str, template_components: list[dict]) -> TemplateCreationResponse:
        """
        Создает шаблон и его элементы

        Args:
            user: данные о пользователе
            name: название шаблона
            template_components: список элементов (объемный)

        Returns:
            Идентификатор шаблона
        """
        template = Template(
            user_id=user.sub,
            course_id=user.course_id,
            name=name,
        )
        template = await self.repository.create(template)
        await self.elements_service.create(template.id, self._map_parser_items(template_components))

        self.logger.info(f"Сохранен черновик шаблона: id {template.id}")
        return TemplateCreationResponse(id=template.id)

    async def get(self, user: User, template_id: uuid.UUID) -> TemplateDetailResponse:
        """Получить шаблон с элементами по идентификатору"""
        template = await self._get(user, template_id)
        TemplateAccessVerifier(template).is_valid_course(user)

        return TemplateDetailResponse(
            id=template_id,
            name=template.name,
            is_draft=template.is_draft,
            max_score=template.max_score,
            user=user,
            elements=[
                TemplateElementDto(
                    element_id=element.element_id,
                    element_type=element.element_type,
                    parent_id=element.parent_element_id,
                    properties=element.properties
                ) for element in template.elements
            ]
        )

    async def update(self, user: User, template_id: uuid.UUID, modifiers: TemplateUpdateRequest):
        """Обновить шаблон и/или его элементы"""
        template = await self._get(user, template_id)
        TemplateAccessVerifier(template).is_valid_course(user)

        template.name = modifiers.name if modifiers.name else template.name
        template.max_score = modifiers.max_score if modifiers.max_score else template.max_score

        await self._modify_elements(template_id, modifiers.elements)
        await self.repository.update(template)
        self.logger.info(f"Шаблон обновлен: id {template_id}")

    async def publish(self, user: User, template_id: uuid.UUID, ags_service: AgsService):
        """Опубликовать шаблон"""
        template = await self._get(user, template_id)
        TemplateAccessVerifier(template).is_valid_course(user).can_publish()

        template.is_draft = False
        await self.repository.update(template)

        ags_service.find_or_create_lineitem(template)  # TODO background
        self.logger.info(f"Шаблон опубликован: id {template_id}")

    async def delete(self, user: User, template_id: uuid.UUID, file_service: ChainStorage, ags_service: AgsService):
        """Удалить шаблон, его элементы и медиа-файлы элементов"""
        template = await self._get(user, template_id)
        TemplateAccessVerifier(template).is_valid_course(user)

        media_to_delete = await self.elements_service.get_media_keys_in_elements(template_id)
        await self.repository.delete(user.course_id, template_id)

        ags_service.delete_lineitem(template_id)  # TODO background
        for media in media_to_delete:  # TODO background
            file_service.remove(media)
        self.logger.info(f"Шаблон удален: id {template_id}")

    async def get_all_by_course_user(self, user: User, course: CourseService) -> TemplateCourseCollection:
        """Получить все шаблоны для пользователя по курсу"""
        templates = await self.repository.get_all_by_course_user(user.course_id, user.sub,
                                                                 UserRole.TEACHER in user.roles)
        return TemplateCourseCollection(
            course_name=course.name,
            user=user,
            templates=[
                TemplateCourseSummary(
                    id=template.id,
                    name=template.name,
                    is_draft=template.is_draft,
                    user=user,
                    reports=[
                        MinimalReport(**report.model_dump()) for report in template.reports if
                        report.author_id == user.sub
                    ]
                ) for template in templates
            ]
        )

    async def _get(self, user: User, template_id: uuid.UUID) -> Template:
        template = await self.repository.get(user.sub, template_id)
        if not template:
            raise TemplateNotFoundException(template_id)
        return template

    async def _modify_elements(self, template_id: uuid.UUID, modifiers: Sequence[TemplateElementUpdateUnit]):
        """Модифицирует элементы шаблона"""
        buckets = defaultdict(list)
        for modifier in modifiers:
            buckets[modifier.action].append(modifier)

        await self.elements_service.delete(template_id, buckets[TemplateElementUpdateAction.DELETE])
        await self.elements_service.create(template_id, buckets[TemplateElementUpdateAction.CREATE])
        await self.elements_service.update(template_id, buckets[TemplateElementUpdateAction.UPDATE])

    def _map_parser_items(self, items: Sequence[dict]) -> Sequence[CreateTemplateElementDto]:
        """
        !!!ВРЕМЕННЫЙ, ПОДЛЕЖИТ УДАЛЕНИЮ!!!
        Маппит сырые данные из парсера в минимально необходимое представление
        """
        mapped_items = []
        for item in items:
            mapped_item = CreateTemplateElementDto.model_construct(**item)
            if isinstance(mapped_item.data, list):
                mapped_item.data = self._map_parser_items(mapped_item.data)
            mapped_items.append(mapped_item)
        return mapped_items
