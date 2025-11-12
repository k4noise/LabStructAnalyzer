import uuid

from fastapi import APIRouter, UploadFile, Depends
from fastapi.params import File
from fastapi_hypermodel import HALResponse
from starlette import status
from starlette.responses import JSONResponse, Response

from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.core.dependencies import get_template_service, get_report_service, \
    get_user_with_any_role, get_user, get_file_storage, get_course_service, get_ags_service, \
    get_nrps_service
from labstructanalyzer.schemas.report import ReportCreationResponse, AllReportsByUserResponse

from labstructanalyzer.schemas.template import TemplateDetailResponse, TemplateCourseCollection, TemplateUpdateRequest, \
    TemplateCreationResponse

from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.course import CourseService
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.services.parser.common import ParserService

from labstructanalyzer.services.template import TemplateService
from labstructanalyzer.services.report import ReportService
from labstructanalyzer.utils.files.hybrid_storage import HybridStorage

router = APIRouter()


@router.post(
    "",
    response_model=TemplateCreationResponse,
    response_class=HALResponse,
    summary="Преобразовать шаблон из docx в json",
    description="Принимает файл формата `.docx`, применяет структуру и возвращает JSON-компоненты.",
    tags=["Template"],
    responses={
        200: {
            "description": "Успешное преобразование шаблона",
            "content": {
                "application/json": {
                    "example": {"id": "c72869cb-8ac0-48b7-936f-370917e82b8e"}
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
    """Парсит шаблон на структурные элементы и сохраняет его"""
    parser_service = ParserService()

    template_components = await parser_service.get_structured_components(template)
    return await template_service.create(user, parser_service.get_name(template),
                                         template_components)


@router.patch(
    "/{template_id}",
    summary="Сохранить новые данные шаблона",
    description="Обновляет существующие данные, заменяя их новыми пользовательскими данными",
    tags=["Template"],
    responses={
        204: {
            "description": "Данные шаблона обновлены успешно",
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
        modified_template: TemplateUpdateRequest,
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER)),
        template_service: TemplateService = Depends(get_template_service)
):
    """Сохранить изменения в шаблоне"""
    await template_service.update(user, template_id, modified_template)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/all",
    response_model=TemplateCourseCollection,
    response_class=HALResponse,
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
    """Получить все шаблона курса"""
    return await template_service.get_all_by_course_user(user, course_service)


@router.post(
    "/{template_id}/publish",
    summary="Публикует шаблон",
    description="Для публикации необходим доступ к службе оценок AGS",
    tags=["Template"],
    responses={
        204: {
            "description": "Данные шаблона обновлены успешно",
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
    """Опубликовать шаблон и создать для него линию оценок"""
    await template_service.publish(user, template_id, ags_service)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{template_id}",
    response_model=TemplateDetailResponse,
    response_class=HALResponse,
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
                        "wrong_role": {
                            "description": "Доступ запрещен. Требуется роль преподавателя",
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
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER)),
        template_service: TemplateService = Depends(get_template_service)
):
    """Получить шаблон отчета для редактирования"""
    return await template_service.get(user, template_id)


@router.delete(
    "/{template_id}",
    summary="Удалить шаблон",
    description="Удаляет шаблон и все его дочерние элементы (включая файлы)",
    tags=["Template"],
    responses={
        204: {
            "description": "Шаблон удален успешно",
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
        file_storage: HybridStorage = Depends(get_file_storage)
):
    """Удалить шаблон, отчеты, ответы"""
    await template_service.delete(user, template_id, file_storage, ags_service)
    return JSONResponse({"detail": "Шаблон успешно удален"})


@router.post(
    "/{template_id}/reports",
    response_model=ReportCreationResponse,
    response_class=HALResponse,
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
        template_service: TemplateService = Depends(get_template_service),
        report_service: ReportService = Depends(get_report_service)
):
    """Создает отчет с данными из старого, если он был"""
    template = await template_service.get(user, template_id)
    return await report_service.create(user, template)


@router.get("/{template_id}/reports",
            tags=["Template", "Report"],
            summary="Получить все отчеты по шаблону",
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
            })
async def get_reports_by_template(
        template_id: uuid.UUID,
        user: User = Depends(get_user),
        report_service: ReportService = Depends(get_report_service),
        template_service: TemplateService = Depends(get_template_service),
        nrps_service: NrpsService = Depends(get_nrps_service)
):
    """
    Получает краткую информацию о всех доступных версиях отчетов всех обучающихся курса конкретного шаблона,
    доступных для отображения согласно статусу (отправлен на (повторную) проверку / проверен)
    """
    template = await template_service.get(user, template_id)
    return await report_service.get_all_by_template(template, user, nrps_service)


@router.get("/{template_id}/reports?author_id={author_id}&status={report_status}",
            tags=["Template", "Report"],
            summary="Получить все отчеты заданного статуса по шаблону",
            response_model=AllReportsByUserResponse,
            response_class=HALResponse,
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
async def get_graded_reports_by_user_and_template(
        template_id: uuid.UUID,
        author_id: str,
        report_status: str,
        user: User = Depends(get_user),
        report_service: ReportService = Depends(get_report_service),
        template_service: TemplateService = Depends(get_template_service),
):
    """Получает краткую информацию о всех доступных отчетов заданного статуса
    конкретного обучающегося курса конкретного шаблона
    """
    template = await template_service.get(user, template_id)
    return await report_service.get_all_by_template_and_status(user, template, author_id, report_status)
