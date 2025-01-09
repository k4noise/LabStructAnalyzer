import uuid
from urllib.request import Request

from fastapi import APIRouter, Depends
from fastapi_another_jwt_auth import AuthJWT
from starlette import status
from starlette.responses import JSONResponse

from labstructanalyzer.configs.config import tool_conf
from labstructanalyzer.core.dependencies import get_report_service, get_answer_service, get_template_service
from labstructanalyzer.models.dto.answer import UpdateScoreAnswerDto, UpdateAnswerDto
from labstructanalyzer.models.dto.report import ReportDto
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.services.pylti1p3.cache import FastAPICacheDataStorage
from labstructanalyzer.services.pylti1p3.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.pylti1p3.request import FastAPIRequest
from labstructanalyzer.services.report import ReportService
from labstructanalyzer.services.template import TemplateService
from labstructanalyzer.utils.rbac_decorator import roles_required

router = APIRouter()


@roles_required(["student"])
@router.patch("/{report_id}")
async def update_answers(
        report_id: uuid.UUID,
        answers: list[UpdateAnswerDto],
        authorize: AuthJWT = Depends(),
        answers_service: AnswerService = Depends(get_answer_service)
):
    """
    Обновить некоторые ответы в отчете.
    """
    await answers_service.update_answers(report_id, answers)


@router.get("/{report_id}")
async def get_report(
        report_id: uuid.UUID,
        request: Request,
        authorize: AuthJWT = Depends(),
        report_service: ReportService = Depends(get_report_service)
):
    """
    Получить отчет по id вне зависимости от его статуса. Включает в себя данные об ответах и оценках.
    Производится проверка прав: доступ разрешен любому преподавателю или ассистенту

    Возвращает предыдущие (если были) и текущие ответы, все существующие оценки
    для студента производится проверка, он ли автор
    преподавателю и ассистенту доступ свободный
    """
    roles = authorize.get_raw_jwt().get("roles")
    if len(roles) == 1 and "student" in roles:
        is_author = await report_service.check_is_author(report_id, authorize.get_jwt_subject())
        if not is_author:
            return JSONResponse(
                {"detail": "Доступ запрещен: Вы не являетесь автором отчета"},
                status_code=status.HTTP_403_FORBIDDEN
            )

    current_report = await report_service.get_by_id(report_id)
    prev_report = await report_service.get_prev_report(current_report)

    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(authorize.get_raw_jwt().get("launch_id"),
                                                     FastAPIRequest(request),
                                                     tool_conf,
                                                     launch_data_storage=launch_data_storage)
    nrps_service = NrpsService(message_launch)
    return ReportDto(
        template=current_report.template,
        report_id=current_report.report_id,
        status=current_report.status,
        grader_name=nrps_service.get_user_name(current_report.grader_id) if current_report.grader_id else None,
        current_answers=current_report.answers,
        prev_answers=prev_report.answers if prev_report else None
    )


@roles_required(['teacher', 'assistant'])
@router.post("/{report_id}/grade")
async def save_grades(
        report_id: uuid.UUID,
        score_data: list[UpdateScoreAnswerDto],
        request: Request,
        authorize: AuthJWT = Depends(),
        answers_service: AnswerService = Depends(get_answer_service),
        report_service: ReportService = Depends(get_report_service),
        template_service: TemplateService = Depends(get_template_service)
):
    """
    Сохранить оценки, подсчитать итоговый балл, перенести в LMS
    """
    await answers_service.bulk_update_grades(report_id, score_data)
    template = await template_service.get_by_report_id(report_id)

    final_grade = await answers_service.calc_final_score(report_id, template.max_score)
    await report_service.set_grade(report_id, final_grade)

    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(authorize.get_raw_jwt().get("launch_id"),
                                                     FastAPIRequest(request),
                                                     tool_conf,
                                                     launch_data_storage=launch_data_storage)
    ags_service = AgsService(message_launch)
    ags_service.set_grade(
        template,
        authorize.get_jwt_subject(),
        final_grade
    )
