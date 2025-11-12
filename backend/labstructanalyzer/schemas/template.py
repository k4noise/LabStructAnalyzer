from __future__ import annotations

import uuid
from typing import Optional, Sequence

from fastapi_hypermodel import HALLinks, FrozenDict, HALFor
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

from labstructanalyzer.domain.report_status import ReportStatus
from labstructanalyzer.models.report import Report

from labstructanalyzer.models.template import Template
from labstructanalyzer.models.user_model import User
from labstructanalyzer.schemas.answer import AnswerResponse, PreGradedAnswerResponse
from labstructanalyzer.schemas.report import MinimalReportResponse
from labstructanalyzer.schemas.template_element import TemplateElementResponse, TemplateElementUpdateRequest
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.utils.hal_hypermodel import HALHyperModel


class TemplateStructure(BaseModel):
    """Модель структуры шаблона"""
    id: uuid.UUID
    name: str
    max_score: int
    elements: Sequence[TemplateElementResponse]
    is_draft: Optional[bool] = None

    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True, alias_generator=to_camel,
                              from_attributes=True)

    @staticmethod
    def from_domain(template: Template) -> "TemplateStructure":
        return TemplateStructure(
            id=template.id,
            name=template.name,
            max_score=template.max_score,
            elements=[TemplateElementResponse.from_domain(element) for element in template.elements]
        )


class TemplateUpdateRequest(TemplateStructure):
    """Данные для обновления шаблона"""
    name: Optional[str] = None
    max_score: Optional[int] = None
    elements: Optional[Sequence[TemplateElementUpdateRequest]]


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

    @staticmethod
    def from_domain(template: Template, user: User) -> "TemplateDetailResponse":
        return TemplateDetailResponse(
            id=template.id,
            name=template.name,
            is_draft=template.is_draft,
            max_score=template.max_score,
            user=user,
            elements=[TemplateElementResponse.from_domain(element) for element in template.elements]
        )


class TemplateCourseSummary(HALHyperModel):
    """Сводная информация о шаблоне в контексте курса с отчетами"""
    id: uuid.UUID
    name: str
    is_draft: bool
    reports: Sequence[MinimalReportResponse] = Field(default_factory=list)

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

    @staticmethod
    def from_domain(template: Template, user: User) -> "TemplateCourseSummary":
        return TemplateCourseSummary(
            id=template.id,
            name=template.name,
            is_draft=template.is_draft,
            user=user,
            reports=[
                MinimalReportResponse.from_domain(report) for report in template.reports if
                report.author_id == user.sub
            ]
        )


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

    @staticmethod
    def from_domain(templates: Sequence[Template], user: User, course_name: str) -> "TemplateCourseCollection":
        return TemplateCourseCollection(
            course_name=course_name,
            user=user,
            templates=[TemplateCourseSummary.from_domain(template, user) for template in templates]
        )


class FullWorkResponse(HALHyperModel):
    """Детальный ответ с данными отчёта и шаблона"""
    template: "TemplateStructure"
    id: uuid.UUID
    status: ReportStatus
    grader_name: Optional[str] = None
    score: Optional[float] = None
    answers: Sequence[AnswerResponse | PreGradedAnswerResponse]

    # Поля используются только для условной генерации ссылок HAL
    author_id: str = Field(exclude=True)
    user: User = Field(exclude=True)

    links: HALLinks = FrozenDict({
        "self": HALFor("get_report", {"report_id": "<id>"}),
        "save": HALFor(
            "save_grades",
            {"report_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_student(),
        ),
        "submit": HALFor(
            "send_to_grade",
            {"report_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_student(),
        ),
        "unsubmit": HALFor(
            "cancel_send_to_grade",
            {"report_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_student(),
        ),

        "grade": HALFor(
            "save_grades",
            {"report_id": "<id>"},
            condition=lambda values:
            values["user"] and
            values["user"].is_instructor() and
            not values["user"].sub == values["author_id"],
        )
    })

    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True, alias_generator=to_camel)

    @staticmethod
    def from_domain(report: Report, user: User, nrps: NrpsService) -> "FullWorkResponse":
        elements_by_id_map = {element.id: element for element in report.template.elements}

        dto_factory = PreGradedAnswerResponse.from_domain if user.is_instructor() and not user.sub == report.author_id else AnswerResponse.from_domain

        return FullWorkResponse(
            template=TemplateStructure.from_domain(report.template),
            id=report.id,
            status=report.status,
            score=report.score,
            answers=[
                dto_factory(answer, elements_by_id_map)
                for answer in report.answers
            ],
            user=user,
            author_id=report.author_id,
            **({"grader_name": nrps.get_user_by_id(report.grader_id)} if report.grader_id is not None else {}))
