from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Sequence

from fastapi_hypermodel import HALLinks, FrozenDict, HALFor
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from labstructanalyzer.domain.report_status import ReportStatus
from labstructanalyzer.models.report import Report
from labstructanalyzer.models.user_model import User
from labstructanalyzer.schemas.user import NrpsUser
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.utils.hal_hypermodel import HALHyperModel


class ReportCreationResponse(HALHyperModel):
    """id созданного отчета"""
    id: uuid.UUID

    links: HALLinks = FrozenDict({
        "self": HALFor("create_report"),
        "get": HALFor("get_report", {"report_id": "<id>"})
    })


class MinimalReportResponse(BaseModel):
    """Упрощённое представление отчёта по шаблону"""
    updated_at: datetime
    report_id: uuid.UUID
    status: ReportStatus

    # Поле используется только для условной генерации ссылок HAL
    user: User = Field(exclude=True)

    links: HALLinks = FrozenDict({
        "self": HALFor("get_report", {"report_id": "<id>"}),
        "create_report": HALFor(
            "create_report",
            {"template_id": "<id>"},
            condition=lambda values: values["user"] and values["user"].is_student(),
        ),
    })

    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True, alias_generator=to_camel)

    @staticmethod
    def from_domain(report: Report) -> "MinimalReportResponse":
        return MinimalReportResponse(
            updated_at=report.updated_at,
            report_id=report.id,
            status=report.status,
        )


class MinimalReportInfoResponse(MinimalReportResponse):
    """Расширенное упрощённое представление отчёта с информацией об авторе"""
    author_name: str
    score: Optional[float] = None

    @staticmethod
    def from_domain_with_user(report: Report, author: NrpsUser) -> "MinimalReportInfoResponse":
        return MinimalReportInfoResponse(
            **MinimalReportResponse.from_domain(report).model_dump(by_alias=True),
            author_name=author.name,
            score=report.score
        )


class AllReportsResponse(BaseModel):
    """Коллекция всех отчётов по шаблону"""
    template_name: str
    template_id: uuid.UUID
    max_score: float
    self_reports: Optional[Sequence[MinimalReportInfoResponse]] = Field(default=None)
    other_reports: Optional[Sequence[MinimalReportInfoResponse]] = Field(default=None)

    # Поле используется только для условной генерации ссылок HAL
    user: User = Field(exclude=True)

    links: HALLinks = FrozenDict({
        "self": HALFor("get_report"),
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
    def from_domain(template: "TemplateDetailResponse", all_reports: Sequence[Report],
                    user: User, nrps: NrpsService) -> "AllReportsResponse":
        return AllReportsResponse(
            template_name=template.name,
            template_id=template.id,
            max_score=template.max_score,
            user=user,
            **({
                   "self_reports": [
                       MinimalReportInfoResponse.from_domain_with_user(report, nrps.get_user_by_id(report.author_id))
                       for
                       report in all_reports
                       if
                       report.author_id == user.sub]
               } if not user.is_teacher() else {}),
            **({
                   "other_reports": [
                       MinimalReportInfoResponse.from_domain_with_user(report, nrps.get_user_by_id(report.author_id))
                       for
                       report in all_reports if report.author_id != user.sub]
               } if user.is_instructor() else {})
        )
