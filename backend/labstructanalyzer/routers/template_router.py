import uuid

from fastapi import APIRouter, UploadFile, Depends
from fastapi.params import File
from starlette.responses import JSONResponse

from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.core.dependencies import get_template_service, get_report_service, get_answer_service, \
    get_user_with_any_role, get_user, get_chain_storage, get_course_service, get_ags_service, \
    get_nrps_service

from labstructanalyzer.schemas.template import TemplateWithElementsDto, AllContentFromCourse, TemplateToModify

from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.course import CourseService
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.services.parser.common import ParserService

from labstructanalyzer.services.template import TemplateService
from labstructanalyzer.services.report import ReportService, ReportStatus
from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.utils.files.chain_storage import ChainStorage

router = APIRouter()


@router.post(
    "",
    summary="Преобразовать шаблон из docx в json",
    description="Принимает файл формата `.docx`, применяет структуру и возвращает JSON-компоненты.",
    tags=["Template"],
    responses={
        200: {
            "description": "Успешное преобразование шаблона",
            "content": {
                "application/json": {
                    "example": {"template_id": "c72869cb-8ac0-48b7-936f-370917e82b8e"}
                }
            }
        },
        401: {
            "description": "Неавторизованный доступ",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            }
        },
        404: {
            "description": "Доступ запрещен. Требуется роль преподавателя или ассистента",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        422: {
            "description": "Ошибки парсера",
            "content": {
                "application/json": {
                    "example": {"detail": "Тип файла не поддерживается"}
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
    },
)
async def parse_template(
        template: UploadFile = File(..., description="DOCX файл для обработки"),
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER)),
        template_service: TemplateService = Depends(get_template_service)
):
    """
    Преобразовать шаблон из docx в json, применяя структуру

    Args:
        template: Файл формата `.docx` для обработки
        user: Данные учителя
        template_service: Сервис обработки шаблонов
    """
    parser_service = ParserService()

    template_components = await parser_service.get_structured_components(template)
    template_id = await template_service.create(user, parser_service.get_name(template),
                                                template_components)

    return JSONResponse({"template_id": str(template_id)})


@router.patch(
    "/{template_id}",
    summary="Сохранить новые данные шаблона",
    description="Обновляет существующие данные, заменяя их новыми пользовательскими данными",
    tags=["Template"],
    responses={
        200: {
            "description": "Данные шаблона обновлены успешно",
            "content": {
                "application/json": {
                    "example": {"detail": "Шаблон обновлен успешно"}
                }
            }
        },
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
                            "description": "Доступ запрещен. Требуется роль преподавателя",
                            "value": {"detail": "Не найдено"}
                        },
                        "wrong_course": {
                            "description": "Доступ запрещен. Шаблон другого курса",
                            "value": {"detail": "Не найдено"}
                        },
                        "no_template": {
                            "description": "Шаблон не найден",
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
        },
    },
)
async def save_modified_template(
        template_id: uuid.UUID,
        modified_template: TemplateToModify,
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER)),
        template_service: TemplateService = Depends(get_template_service)
):
    await template_service.update(user, template_id, modified_template)
    return JSONResponse({"detail": "Шаблон обновлен успешно"})


@router.get(
    "/all",
    response_model=AllContentFromCourse,
    summary="Получить все доступные шаблоны и отчеты",
    description="Возвращает все сохраненные для курса пользователя шаблоны, которые не являются черновиками, "
                "для студентов возвращает id и статус отчета",
    tags=["Template"],
    responses={
        200: {
            "description": "Данные шаблонов (и отчетов)",
        },
        401: {
            "description": "Неавторизованный доступ",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
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
    },
)
async def get_templates(
        user: User = Depends(get_user),
        template_service: TemplateService = Depends(get_template_service),
        course_service: CourseService = Depends(get_course_service)
):
    return await template_service.get_all_by_course_user(user, course_service)


@router.post(
    "/{template_id}/publish",
    summary="Публикует шаблон",
    description="Для публикации необходим доступ к службе оценок AGS",
    tags=["Template"],
    responses={
        200: {
            "description": "Данные шаблона обновлены успешно",
            "content": {
                "application/json": {
                    "example": {"detail": "Шаблон обновлен успешно"}
                }
            }
        },
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
                            "description": "Доступ запрещен. Требуется роль преподавателя",
                            "value": {"detail": "Не найдено"}
                        },
                        "wrong_course": {
                            "description": "Доступ запрещен. Шаблон другого курса",
                            "value": {"detail": "Не найдено"}
                        },
                        "no_template": {
                            "description": "Шаблон не найден",
                            "value": {"detail": "Не найдено"}
                        }
                    }
                }
            }
        },
        409: {
            "description": "Публикация уже опубликованного шаблона",
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
    },
)
async def publish_template(
        template_id: uuid.UUID,
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER)),
        template_service: TemplateService = Depends(get_template_service),
        ags_service: AgsService = Depends(get_ags_service)
):
    await template_service.publish(user, template_id, ags_service)
    return JSONResponse({"detail": "Шаблон обновлен успешно"})


@router.get(
    "/{template_id}",
    response_model=TemplateWithElementsDto,
    summary="Получить данные шаблона",
    description="Возвращает свойства шаблона и все дочерние элементы",
    tags=["Template"],
    responses={
        200: {
            "description": "Данные шаблона",
        },
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
                        "wrong_course": {
                            "description": "Доступ запрещен. Шаблон другого курса",
                            "value": {"detail": "Не найдено"}
                        },
                        "no_template": {
                            "description": "Шаблон не найден",
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
        },
    },
)
async def get_template(
        template_id: uuid.UUID,
        user: User = Depends(get_user),
        template_service: TemplateService = Depends(get_template_service)
):
    return await template_service.get(user, template_id)


@router.delete(
    "/{template_id}",
    summary="Удалить шаблон",
    description="Удаляет шаблон и все его дочерние элементы (включая файлы)",
    tags=["Template"],
    responses={
        200: {
            "description": "Шаблон удален успешно",
            "content": {
                "application/json": {
                    "example": {"detail": "Шаблон успешно удален"}
                }
            }
        },
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
                            "description": "Доступ запрещен. Требуется роль преподавателя",
                            "value": {"detail": "Не найдено"}
                        },
                        "wrong_course": {
                            "description": "Доступ запрещен. Шаблон другого курса",
                            "value": {"detail": "Не найдено"}
                        },
                        "no_template": {
                            "description": "Шаблон не найден",
                            "value": {"detail": "Не найдено"}
                        }
                    }
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
    },
)
async def remove_template(
        template_id: uuid.UUID,
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER)),
        template_service: TemplateService = Depends(get_template_service),
        ags_service: AgsService = Depends(get_ags_service),
        chain_storage: ChainStorage = Depends(get_chain_storage)
):
    await template_service.delete(user, template_id, chain_storage, ags_service)
    return JSONResponse({"detail": "Шаблон успешно удален"})


@router.post(
    "/{template_id}/reports",
    tags=["Template", "Report"],
    summary="Создать отчет с ответами на основе шаблона",
    responses={
        200: {
            "description": "Отчет успешно создан",
            "content": {
                "application/json": {
                    "example": {"id": "12345"}
                }
            }
        },
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
                        "no_template": {
                            "description": "Шаблон не найден",
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
        },
    }
)
async def create_report(
        template_id: uuid.UUID,
        user: User = Depends(get_user_with_any_role(UserRole.STUDENT)),
        report_service: ReportService = Depends(get_report_service),
        template_service: TemplateService = Depends(get_template_service),
        answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Создать отчет на основе данных из шаблона, если это возможно
    """
    last_report = await report_service.get_last_by_author(user, template_id)
    if last_report.status != ReportStatus.GRADED:
        return JSONResponse({"id": str(last_report.report_id)})

    report_id = await report_service.create(user, template_id)
    template = await template_service.get(user, template_id)
    await answer_service.create(report_id, template.elements)

    return JSONResponse({"id": str(report_id)})


@router.get("/{template_id}/reports",
            tags=["Template", "Report"],
            summary="Получить все шаблоны по отчету",
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
                                    "description": "Доступ запрещен. Требуется роль преподавателя",
                                    "value": {"detail": "Не найдено"}
                                },
                                "wrong_course": {
                                    "description": "Доступ запрещен. Шаблон другого курса",
                                    "value": {"detail": "Не найдено"}
                                },
                                "no_template": {
                                    "description": "Шаблон не найден",
                                    "value": {"detail": "Не найдено"}
                                }
                            }
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
async def get_reports_by_template(
        template_id: uuid.UUID,
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER, UserRole.ASSISTANT)),
        report_service: ReportService = Depends(get_report_service),
        template_service: TemplateService = Depends(get_template_service),
        nrps_service: NrpsService = Depends(get_nrps_service)
):
    """
    Получает краткую информацию о всех доступных версиях отчетов всех обучающихся курса конкретного шаблона,
    доступных для отображения согласно статусу (отправлен на (повторную) проверку / проверен)
    """
    template = await template_service.get(user, template_id)
    return await report_service.get_all_by_template(template, nrps_service)
