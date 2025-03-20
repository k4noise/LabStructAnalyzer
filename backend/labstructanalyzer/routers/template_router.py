import json
import os
import uuid

from fastapi import APIRouter, UploadFile, HTTPException, Depends
from fastapi.params import File
from starlette.requests import Request
from starlette.responses import JSONResponse

from labstructanalyzer.main import global_logger
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.configs.config import CONFIG_DIR, TOOL_CONF, TEMPLATE_IMAGE_PREFIX
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.core.dependencies import get_template_service, get_report_service, get_answer_service, \
    get_user_with_any_role, get_user

from labstructanalyzer.models.dto.modify_template import TemplateToModify
from labstructanalyzer.models.dto.report import MinimalReportInfoDto, AllReportsDto
from labstructanalyzer.models.dto.template import TemplateWithElementsDto, AllTemplatesDto, \
    TemplateMinimalProperties

from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.course import CourseService
from labstructanalyzer.services.lti.nrps import NrpsService

from labstructanalyzer.services.pylti1p3.cache import FastAPICacheDataStorage
from labstructanalyzer.services.pylti1p3.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.pylti1p3.request import FastAPIRequest

from labstructanalyzer.services.parser.docx import DocxParser
from labstructanalyzer.services.template import TemplateService
from labstructanalyzer.services.report import ReportService, ReportStatus
from labstructanalyzer.services.answer import AnswerService

router = APIRouter()
logger = global_logger.get_logger(__name__)


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
        400: {
            "description": "Ошибка запроса. Файл отсутствует или имеет неподдерживаемый формат",
            "content": {
                "application/json": {
                    "examples": {
                        "no_template_file": {
                            "summary": "Отсутствует файл шаблона",
                            "value": {"detail": "Нет файла шаблона"}
                        },
                        "unsupported_file_type": {
                            "summary": "Неподдерживаемый тип файла",
                            "value": {"detail": "Тип файла не поддерживается"}
                        },
                    }
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
        403: {
            "description": "Доступ запрещен. Требуется роль преподавателя или ассистента",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
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
    if not template:
        raise HTTPException(status_code=400, detail="Нет файла шаблона")

    file_name_parts = os.path.splitext(os.path.basename(template.filename))

    if file_name_parts[1].lower() != ".docx":
        raise HTTPException(status_code=400, detail="Тип файла не поддерживается")

    # TODO ВНИМАНИЕ ХАРДКОД
    file_path = os.path.join(CONFIG_DIR, "structure.json")
    with open(file_path, 'r', encoding='utf-8') as file:
        data_dict = json.load(file)

    docx_parser = DocxParser(await template.read(), data_dict, TEMPLATE_IMAGE_PREFIX)
    template_components = docx_parser.get_structure_components()
    template_model = await template_service.create(user.sub, user.course_id, file_name_parts[0],
                                                   template_components)

    logger.info(f"Сохранен черновик шаблона: id {template_model.template_id}")
    return JSONResponse({"template_id": str(template_model.template_id)})


@router.patch(
    "/{template_id}",
    summary="Сохранить новые данные шаблона",
    description="Обновляет существующие данные, заменяя их новыми пользовательскими данными.\n"
                "Для публикации шаблона необходим доступ к службе оценок AGS",
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
        403: {
            "description": "Доступ запрещен. Требуется роль преподавателя",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Шаблон не найден",
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
    },
)
async def save_modified_template(
        request: Request,
        template_id: uuid.UUID,
        modified_template: TemplateToModify,
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER)),
        template_service: TemplateService = Depends(get_template_service)
):
    template = await template_service.update(template_id, modified_template)

    if not modified_template.is_draft:
        launch_data_storage = FastAPICacheDataStorage(cache)
        message_launch = FastAPIMessageLaunch.from_cache(user.launch_id,
                                                         FastAPIRequest(request),
                                                         TOOL_CONF,
                                                         launch_data_storage=launch_data_storage)
        AgsService(message_launch).create_lineitem(template)

    logger.info(f"Шаблон обновлен: id {template.template_id}")
    return JSONResponse({"detail": "Шаблон обновлен успешно"})


@router.get(
    "/all",
    response_model=AllTemplatesDto,
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
async def get_templates(request: Request,
                        user: User = Depends(get_user),
                        template_service: TemplateService = Depends(get_template_service)
                        ):
    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(user.launch_id, FastAPIRequest(request), TOOL_CONF,
                                                     launch_data_storage=launch_data_storage)

    course_name = CourseService(message_launch).get_name()

    has_full_access = UserRole.TEACHER in user.roles
    has_partial_access = UserRole.ASSISTANT in user.roles
    with_reports = not (has_full_access or has_partial_access)

    templates_with_base_properties = await template_service.get_all_by_course(user.course_id, user.sub,
                                                                              with_reports=with_reports)

    data = AllTemplatesDto(
        can_upload=has_full_access,
        can_grade=has_full_access or has_partial_access,
        course_name=course_name,
        templates=[
            TemplateMinimalProperties(
                template_id=item[0],
                name=item[1],
                report_id=item[2] if len(item) > 2 else None,
                report_status=ReportStatus[item[3]] if len(item) > 3 and item[3] is not None else None
            ) for
            item in
            templates_with_base_properties],

    )
    if has_full_access:
        drafts_with_base_properties = await template_service.get_all_by_course(user.course_id, user.sub, True)
        data.drafts = [TemplateMinimalProperties(template_id=item[0], name=item[1]) for item in
                       drafts_with_base_properties]
    return data


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
            "description": "Шаблон не найден",
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
    },
)
async def get_template(
        template_id: uuid.UUID,
        user: User = Depends(get_user),
        template_service: TemplateService = Depends(get_template_service)
):
    template = await template_service.get_by_id(template_id)
    if template:
        elements = template_service.build_hierarchy(template.elements)
        can_edit = UserRole.TEACHER in user.roles
        can_grade = can_edit or UserRole.ASSISTANT in user.roles

        return TemplateWithElementsDto(
            template_id=template_id,
            name=template.name,
            is_draft=template.is_draft,
            max_score=template.max_score,
            can_edit=can_edit,
            can_grade=can_grade,
            elements=elements
        )


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
        403: {
            "description": "Доступ запрещен. Требуется роль преподавателя",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Шаблон не найден",
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
    },
)
async def remove_template(
        request: Request,
        template_id: uuid.UUID,
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER)),
        template_service: TemplateService = Depends(get_template_service)
):
    await template_service.delete(template_id)
    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(user.launch_id,
                                                     FastAPIRequest(request),
                                                     TOOL_CONF,
                                                     launch_data_storage=launch_data_storage)

    ags_service = AgsService(message_launch)
    ags_service.delete_lineitem(template_id)

    logger.info(f"Шаблон удален: id {template_id}")
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
        403: {
            "description": "Доступ запрещен. Требуется роль студента",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Шаблон не найден",
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
async def create_report(
        template_id: uuid.UUID,
        user: User = Depends(get_user_with_any_role(UserRole.STUDENT)),
        report_service: ReportService = Depends(get_report_service),
        template_service: TemplateService = Depends(get_template_service),
        answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Создать отчет на основе данных из шаблона
    """
    template = await template_service.get_by_id(template_id)
    report_id = await report_service.create(template_id, user.sub)
    await answer_service.create_answers(template, report_id)

    logger.info(
        f"Отчет для пользователя с id {user.sub} создан: id {report_id} на основе шаблона с id{template_id}")
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
                403: {
                    "description": "Доступ запрещен. Требуется роль преподавателя или ассистента",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Доступ запрещен"}
                        }
                    }
                },
                404: {
                    "description": "Шаблон или отчет не найден",
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
async def get_reports_by_template(
        template_id: uuid.UUID,
        request: Request,
        user: User = Depends(get_user_with_any_role(UserRole.TEACHER, UserRole.ASSISTANT)),
        template_service: TemplateService = Depends(get_template_service)
):
    """
    Получает краткую информацию о всех доступных версиях отчетов всех обучающихся курса конкретного шаблона,
    доступных для отображения согласно статусу (отправлен на (повторную) проверку / проверен)
    """
    all_reports = await template_service.get_all_reports(template_id)
    template = await template_service.get_by_id(template_id)
    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(user.launch_id,
                                                     FastAPIRequest(request),
                                                     TOOL_CONF,
                                                     launch_data_storage=launch_data_storage)
    return AllReportsDto(
        template_name=template.name,
        max_score=template.max_score,
        reports=[
            MinimalReportInfoDto(
                report_id=report.report_id,
                date=report.updated_at,
                status=ReportStatus[report.status].value,
                author_name=NrpsService(message_launch).get_user_name(report.author_id),
                score=report.score
            ) for report in all_reports
        ]
    )
