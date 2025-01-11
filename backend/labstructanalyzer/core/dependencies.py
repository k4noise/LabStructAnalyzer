from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.core.database import get_session
from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.services.report import ReportService
from labstructanalyzer.services.template import TemplateService, TemplateElementService


def get_template_service(session: AsyncSession = Depends(get_session)) -> TemplateService:
    return TemplateService(session)


def get_report_service(session: AsyncSession = Depends(get_session)) -> ReportService:
    return ReportService(session)


def get_answer_service(session: AsyncSession = Depends(get_session)) -> AnswerService:
    return AnswerService(session)
