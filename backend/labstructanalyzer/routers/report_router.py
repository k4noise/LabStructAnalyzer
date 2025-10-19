import uuid
from typing import Sequence

from fastapi import APIRouter, Depends
from fastapi_hypermodel import HALResponse

from labstructanalyzer.core.logger import GlobalLogger
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.core.dependencies import get_report_service, get_user_with_any_role, get_user, get_grade_service, \
    get_nrps_service

from labstructanalyzer.schemas.answer import UpdateAnswerDataRequest, UpdateAnswerScoresRequest
from labstructanalyzer.schemas.template import FullWorkResponse
from labstructanalyzer.services.grade import GradeService
from labstructanalyzer.services.lti.nrps import NrpsService

from labstructanalyzer.services.report import ReportService

router = APIRouter()
logger = GlobalLogger().get_logger(__name__)


@router.get(
    "/{report_id}",
    tags=["Report"],
    response_class=HALResponse,
    response_model=FullWorkResponse,
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
        404: {
            "description": "Доступ запрещен или шаблон не найден",
            "content": {
                "application/json": {
                    "example": {
                        "wrong_role": {
                            "description": "Доступ запрещен. Требуется роль студента",
                            "value": {"detail": "Не найдено"}
                        },
                        "wrong_course": {
                            "description": "Доступ запрещен. Шаблон другого курса",
                            "value": {"detail": "Не найдено"}
                        },
                        "not_a_author": {
                            "description": "Доступ запрещен. Студент - не автор шаблона",
                            "value": {"detail": "Не найдено"}
                        },
                        "not_for_instructor": {
                            "description": "Доступ запрещен. Отчет недоступен для преподавателя / ассистента",
                            "value": {"detail": "Не найдено"}
                        },
                        "no_report": {
                            "description": "Отчет не найден",
                            "value": {"detail": "Не найдено"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Ошибка БД",
            "content": {
                "application/json": {
                    "example": {
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
        user: User = Depends(get_user),
        report_service: ReportService = Depends(get_report_service),
        nrps_service: NrpsService = Depends(get_nrps_service)
):
    """Получить отчет вместе с шаблоном и оценками"""
    return report_service.get(user, report_id, nrps_service)


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
        404: {
            "description": "Доступ запрещен или шаблон не найден",
            "content": {
                "application/json": {
                    "example": {
                        "wrong_role": {
                            "description": "Доступ запрещен. Требуется роль студента",
                            "value": {"detail": "Не найдено"}
                        },
                        "wrong_course": {
                            "description": "Доступ запрещен. Шаблон другого курса",
                            "value": {"detail": "Не найдено"}
                        },
                        "not_a_author": {
                            "description": "Доступ запрещен. Студент - не автор шаблона",
                            "value": {"detail": "Не найдено"}
                        },
                        "not_for_instructor": {
                            "description": "Доступ запрещен. Отчет недоступен для преподавателя / ассистента",
                            "value": {"detail": "Не найдено"}
                        },
                        "no_report": {
                            "description": "Отчет не найден",
                            "value": {"detail": "Не найдено"}
                        }
                    }
                }
            }
        },
        409: {
            "description": "Переход состояния отчета невозможен",
            "content": {
                "application/json": {
                    "example": {"detail": "Действие невозможно"}
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
        answers: Sequence[UpdateAnswerDataRequest],
        user: User = Depends(get_user_with_any_role(UserRole.STUDENT)),
        report_service: ReportService = Depends(get_report_service)
):
    """Обновить ответы в отчете"""
    await report_service.save(user, report_id, answers)


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
        404: {
            "description": "Доступ запрещен или шаблон не найден",
            "content": {
                "application/json": {
                    "example": {
                        "wrong_role": {
                            "description": "Доступ запрещен. Требуется роль преподавателя / ассистента",
                            "value": {"detail": "Не найдено"}
                        },
                        "wrong_course": {
                            "description": "Доступ запрещен. Шаблон другого курса",
                            "value": {"detail": "Не найдено"}
                        },
                        "no_report": {
                            "description": "Отчет не найден",
                            "value": {"detail": "Не найдено"}
                        }
                    }
                }
            }
        },
        409: {
            "description": "Переход состояния отчета невозможен",
            "content": {
                "application/json": {
                    "example": {"detail": "Действие невозможно"}
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
        score_data: Sequence[UpdateAnswerScoresRequest],
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER, UserRole.ASSISTANT)),
        grade_service: GradeService = Depends(get_grade_service)
):
    """Сохранить оценки, подсчитать итоговый балл, перенести в LMS"""
    await grade_service.grade(user, report_id, score_data)


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
        404: {
            "description": "Доступ запрещен или шаблон не найден",
            "content": {
                "application/json": {
                    "example": {
                        "wrong_role": {
                            "description": "Доступ запрещен. Требуется роль студента",
                            "value": {"detail": "Не найдено"}
                        },
                        "wrong_course": {
                            "description": "Доступ запрещен. Шаблон другого курса",
                            "value": {"detail": "Не найдено"}
                        },
                        "not_a_author": {
                            "description": "Доступ запрещен. Студент - не автор шаблона",
                            "value": {"detail": "Не найдено"}
                        },
                        "not_for_instructor": {
                            "description": "Доступ запрещен. Отчет недоступен для преподавателя / ассистента",
                            "value": {"detail": "Не найдено"}
                        },
                        "no_report": {
                            "description": "Отчет не найден",
                            "value": {"detail": "Не найдено"}
                        }
                    }
                }
            }
        },
        409: {
            "description": "Переход состояния отчета невозможен",
            "content": {
                "application/json": {
                    "example": {"detail": "Действие невозможно"}
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
        grade_service: GradeService = Depends(get_grade_service)
):
    """Отправить отчет на оценку"""
    await grade_service.send_to_grade(user, report_id)


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
        404: {
            "description": "Доступ запрещен или шаблон не найден",
            "content": {
                "application/json": {
                    "example": {
                        "wrong_role": {
                            "description": "Доступ запрещен. Требуется роль студента",
                            "value": {"detail": "Не найдено"}
                        },
                        "wrong_course": {
                            "description": "Доступ запрещен. Шаблон другого курса",
                            "value": {"detail": "Не найдено"}
                        },
                        "not_a_author": {
                            "description": "Доступ запрещен. Студент - не автор шаблона",
                            "value": {"detail": "Не найдено"}
                        },
                        "no_report": {
                            "description": "Отчет не найден",
                            "value": {"detail": "Не найдено"}
                        }
                    }
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
    """Убрать отчет с проверки"""
    await report_service.unsubmit(user, report_id)
    logger.info(f"Отчет снят с проверки: id {report_id}")
