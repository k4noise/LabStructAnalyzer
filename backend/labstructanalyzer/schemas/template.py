import enum
import uuid
from typing import Optional, Sequence, Dict, Any

from fastapi_hypermodel import HALHyperModel, HALLinks, FrozenDict, HALFor
from pydantic import BaseModel, Field

from labstructanalyzer.models.user_model import User
from labstructanalyzer.schemas.report import MinimalReport
from labstructanalyzer.schemas.template_element import TemplateElementDto


class TemplateElementUpdateAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class CreatedTemplateDto(HALHyperModel):
    id: uuid.UUID

    links: HALLinks = FrozenDict({
        "get_template": HALFor("get_template", {"template_id": "<id>"})
    })


class TemplateDto(BaseModel):
    """Краткое DTO шаблона без элементов"""
    template_id: uuid.UUID
    name: str
    is_draft: bool
    max_score: int

    class Config:
        from_attributes = True


class TemplateWithElementsDto(TemplateDto, HALHyperModel):
    """DTO шаблона вместе с элементами"""
    elements: Sequence[TemplateElementDto]

    # Поле используется только для условной генерации ссылок HAL
    user: User = Field(exclude=True)

    links: HALLinks = FrozenDict({
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


class MinimalTemplateDto(HALHyperModel):
    """Шаблон в составе курса (с отчётами)"""
    id: uuid.UUID
    name: str
    is_draft: bool
    reports: Sequence[MinimalReport] = Field(default_factory=list)

    # Поле используется только для условной генерации ссылок HAL
    user: User = Field(exclude=True)

    links: HALLinks = FrozenDict({
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


class AllContentFromCourseDto(HALHyperModel):
    """Все шаблоны по курсу с отчетами"""
    course_name: str
    templates: Sequence[MinimalTemplateDto] = Field(default_factory=list)

    # Поле используется только для условной генерации ссылок HAL
    user: User = Field(exclude=True)

    links: HALLinks = FrozenDict({
        "add_template": HALFor(
            "parse_template",
            condition=lambda values: values["user"] and values["user"].is_teacher()
        )
    })


class TemplateElementUpdateUnit(BaseModel):
    """Операция над элементом шаблона"""
    action: TemplateElementUpdateAction
    element_id: uuid.UUID
    element_type: Optional[str] = None
    properties: Dict[str, Any] | Sequence[TemplateElementDto] = Field(default_factory=dict)


class TemplateToModify(TemplateDto):
    name: Optional[str] = None
    max_score: Optional[int] = None
    elements: Optional[Sequence[TemplateElementUpdateUnit]]
