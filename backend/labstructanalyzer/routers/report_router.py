import asyncio
import uuid

from fastapi import APIRouter, Depends
from starlette.requests import Request

from labstructanalyzer.main import global_logger, executor
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.configs.config import TOOL_CONF
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.core.dependencies import get_report_service, get_answer_service, get_user_with_any_role, \
    get_user, get_background_task_service

from labstructanalyzer.schemas.answer import UpdateAnswerDataDto, AnswerDto, PreGradedAnswerDto, UpdateAnswerScoresDto
from labstructanalyzer.schemas.report import ReportDto
from labstructanalyzer.services.background_task import BackgroundTaskService

from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.services.pre_grader import PreGraderService

from labstructanalyzer.services.pylti1p3.cache import FastAPICacheDataStorage
from labstructanalyzer.services.pylti1p3.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.pylti1p3.request import FastAPIRequest

from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.services.report import ReportService, ReportStatus

router = APIRouter()
logger = global_logger.get_logger(__name__)


@router.patch(
    "/{report_id}",
    tags=["Report"],
    summary="Обновить ответы в отчете",
    responses={
        401: {
            "description": "Неавторизованный доступ",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            }
        },
        403: {
            "description": "Доступ запрещен. Требуется роль студента",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Отчет не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Не найдено"}
                }
            }
        },
        500: {
            "description": "Ошибка со стороны БД",
            "content": {
                "application/json": {
                    "example": {"detail": "Ошибка доступа к данным"}
                }
            }
        },
    }
)
async def update_answers(
        report_id: uuid.UUID,
        answers: list[UpdateAnswerDataDto],
        user: User = Depends(get_user_with_any_role(UserRole.STUDENT)),
        answers_service: AnswerService = Depends(get_answer_service),
        report_service: ReportService = Depends(get_report_service)
):
    """
    Обновить некоторые ответы в отчете.
    """
    await answers_service.update_data(report_id, answers)
    await report_service.mark_as_saved(report_id, user.sub)
    logger.info(f"Обновлены ответы в отчете: id {report_id}")


@router.get(
    "/{report_id}",
    tags=["Report"],
    summary="Получить отчет",
    responses={
        401: {
            "description": "Неавторизованный доступ",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            }
        },
        403: {
            "description": "Доступ запрещен. Требуется роль студента",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Отчет не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Не найдено"}
                }
            }
        },
        500: {
            "description": "Служба NRPS недоступна со стороны LMS или ошибка БД",
            "content": {
                "application/json": {
                    "examples": {
                        "lis_service_error": {
                            "summary": "Отсутствует доступ к службе имен и ролей",
                            "value": {"detail": "Нет доступа к службе имен и ролей"}
                        },
                        "bd_error": {
                            "summary": "Ошибка со стороны БД",
                            "value": {"detail": "Ошибка доступа к данным"}
                        },
                    }
                }
            }
        }
    }
)
async def get_report(
        report_id: uuid.UUID,
        request: Request,
        user: User = Depends(get_user),
        report_service: ReportService = Depends(get_report_service)
):
    """
    Получить отчет по id вне зависимости от его статуса. Включает в себя данные об ответах и оценках.
    Производится проверка прав: доступ разрешен любому преподавателю или ассистенту

    Возвращает текущие ответы и все существующие оценки
    для студента производится проверка, он ли автор
    преподавателю и ассистенту доступ свободный, также им предоставляются данные предварительной оценки
    """
    report = await report_service.get_by_id(report_id)
    if len(user.roles) == 1 and UserRole.STUDENT in user.roles:
        report_service.validate_author(report, user.sub)
    can_grade = UserRole.TEACHER in user.roles or UserRole.ASSISTANT in user.roles
    can_edit = not can_grade and (
            report.status != ReportStatus.SUBMITTED.name and report.status != ReportStatus.GRADED.name)
    answer_model = PreGradedAnswerDto if can_grade else AnswerDto
    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(user.launch_id,
                                                     FastAPIRequest(request),
                                                     TOOL_CONF,
                                                     launch_data_storage=launch_data_storage)
    nrps_service = NrpsService(message_launch)

    return ReportDto(
        template_id=report.template_id,
        can_edit=can_edit,
        can_grade=can_grade,
        report_id=report.report_id,
        status=report.status,
        author_name=nrps_service.get_user_data(report.author_id),
        grader_name=nrps_service.get_user_data(
            report.grader_id) if report.grader_id is not None else None,
        score=report.score,
        answers=[
            answer_model(
                answer_id=answer.answer_id,
                element_id=answer.element_id,
                data=answer.data,
                score=answer.score,
                **({'pre_grade': answer.pre_grade} if hasattr(answer_model, 'pre_grade') else {})
            ) for answer in
            report.answers],
    )


@router.patch(
    "/{report_id}/grade",
    tags=["Report"],
    summary="Оценить отчет",
    responses={
        401: {
            "description": "Неавторизованный доступ",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            }
        },
        403: {
            "description": "Доступ запрещен. Требуется роль студента",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Отчет не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Не найдено"}
                }
            }
        },
        500: {
            "description": "Служба AGS недоступна со стороны LMS или ошибка БД",
            "content": {
                "application/json": {
                    "examples": {
                        "lis_service_error": {
                            "summary": "Отсутствует доступ к службе оценок",
                            "value": {"detail": "Нет доступа к службе оценок"}
                        },
                        "bd_error": {
                            "summary": "Ошибка со стороны БД",
                            "value": {"detail": "Ошибка доступа к данным"}
                        },
                    }
                }
            }
        },
    }
)
async def save_grades(
        report_id: uuid.UUID,
        score_data: list[UpdateAnswerScoresDto],
        request: Request,
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER, UserRole.ASSISTANT)),
        answers_service: AnswerService = Depends(get_answer_service),
        report_service: ReportService = Depends(get_report_service),
):
    """
    Сохранить оценки, подсчитать итоговый балл, перенести в LMS
    """
    await answers_service.update_scores(report_id, score_data)
    report = await report_service.get_by_id(report_id)
    template = report.template
    final_grade = await answers_service.calc_final_score(report_id, template.max_score)

    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(user.launch_id,
                                                     FastAPIRequest(request),
                                                     TOOL_CONF,
                                                     launch_data_storage=launch_data_storage)
    ags_service = AgsService(message_launch)
    ags_service.set_grade(
        template,
        report.author_id,
        final_grade
    )
    await report_service.grade(report_id, user.sub, final_grade)
    logger.info(f"Оценен отчет: id {report_id}")


@router.post(
    "/{report_id}/submit",
    tags=["Report"],
    summary="Отправить отчет на проверку",
    responses={
        401: {
            "description": "Неавторизованный доступ",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            }
        },
        403: {
            "description": "Доступ запрещен. Требуется роль студента",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Отчет не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Не найдено"}
                }
            }
        },
        500: {
            "description": "Ошибка со стороны БД",
            "content": {
                "application/json": {
                    "example": {"detail": "Ошибка доступа к данным"}
                }
            }
        }
    }
)
async def send_to_grade(
        report_id: uuid.UUID,
        user: User = Depends(get_user_with_any_role(UserRole.STUDENT)),
        report_service: ReportService = Depends(get_report_service),
        answer_service: AnswerService = Depends(get_answer_service),
        background_task_service: BackgroundTaskService = Depends(get_background_task_service)
):
    await report_service.submit_to_review(report_id, user.sub)
    answers = await answer_service.collect_full_data(report_id)
    pre_grader_service = PreGraderService(answers)

    future = executor.submit(pre_grader_service.grade)
    asyncio.create_task(background_task_service.handle_task_result(future))
    logger.info(f"Отчет отправлен на проверку: id {report_id}")


@router.delete(
    "/{report_id}/submit",
    tags=["Report"],
    summary="Убрать отчет с проверки",
    responses={
        401: {
            "description": "Неавторизованный доступ",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            }
        },
        403: {
            "description": "Доступ запрещен. Требуется роль студента",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Отчет не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Не найдено"}
                }
            }
        },
        500: {
            "description": "Ошибка со стороны БД",
            "content": {
                "application/json": {
                    "example": {"detail": "Ошибка доступа к данным"}
                }
            }
        }
    }
)
async def cancel_send_to_grade(
        report_id: uuid.UUID,
        user: User = Depends(get_user_with_any_role(UserRole.STUDENT)),
        report_service: ReportService = Depends(get_report_service)
):
    await report_service.cancel_review_submit(report_id, user.sub)
    logger.info(f"Отчет снят с проверки: id {report_id}")
