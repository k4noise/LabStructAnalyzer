import uuid
from typing import Optional, Sequence

from fastapi_hypermodel import HALLinks, FrozenDict, HALFor
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

from labstructanalyzer.models.user_model import User
from labstructanalyzer.schemas.report import MinimalReport
from labstructanalyzer.schemas.template_element import TemplateElementDto, TemplateElementUpdateUnit
from labstructanalyzer.utils.hal_hypermodel import HALHyperModel


class TemplateStructure(BaseModel):
    """Модель структуры шаблона"""
    id: uuid.UUID
    name: str
    max_score: int
    elements: Sequence[TemplateElementDto]
    is_draft: Optional[bool] = None

    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True, alias_generator=to_camel,
                              from_attributes=True)


class TemplateUpdateRequest(TemplateStructure):
    """Данные для обновления шаблона"""
    name: Optional[str] = None
    max_score: Optional[int] = None
    elements: Optional[Sequence[TemplateElementUpdateUnit]]

    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True, alias_generator=to_camel)


class TemplateCreationResponse(HALHyperModel):
    """id созданного шаблона"""
    id: uuid.UUID

    links: HALLinks = FrozenDict({
        "self": HALFor("parse_template"),
        "get_template": HALFor("get_template", {"template_id": "<id>"})
    })


class TemplateDetailResponse(TemplateStructure, HALHyperModel):
    """Полные данные шаблона"""
    # Поле используется только для условной генерации ссылок HAL
    user: User = Field(exclude=True)

    links: HALLinks = FrozenDict({
        "self": HALFor("get_template", {"template_id": "<id>"}),
        "update": HALFor(
            "save_modified_template",
            {"template_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_teacher()
        ),
        "publish": HALFor(
            "publish_template",
            {"template_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_teacher() and values.get("is_draft")
        ),
        "delete": HALFor(
            "remove_template",
            {"template_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_teacher()
        ),
        "all": HALFor("get_templates"),
    })


class TemplateCourseSummary(HALHyperModel):
    """Сводная информация о шаблоне в контексте курса с отчетами"""
    id: uuid.UUID
    name: str
    is_draft: bool
    reports: Sequence[MinimalReport] = Field(default_factory=list)

    # Поле используется только для условной генерации ссылок HAL
    user: User = Field(exclude=True)

    links: HALLinks = FrozenDict({
        "self": HALFor("get_template", {"template_id": "<id>"}),
        "get_template": HALFor(
            "get_template",
            {"template_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_teacher()
        ),
        "get_reports": HALFor(
            "get_reports_by_template",
            {"template_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_instructor(),
        ),
        "create_report": HALFor(
            "create_report",
            {"template_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_student(),
        )
    })

    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True, alias_generator=to_camel)


class TemplateCourseCollection(HALHyperModel):
    """Все шаблоны по курсу с отчетами"""
    course_name: str
    templates: Sequence[TemplateCourseSummary] = Field(default_factory=list)

    # Поле используется только для условной генерации ссылок HAL
    user: User = Field(exclude=True)

    links: HALLinks = FrozenDict({
        "self": HALFor("get_templates"),
        "add_template": HALFor(
            "parse_template",
            condition=lambda values: values["user"] and values["user"].is_teacher()
        )
    })

    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True, alias_generator=to_camel)
