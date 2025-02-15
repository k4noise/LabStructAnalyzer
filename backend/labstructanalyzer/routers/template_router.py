import json
import os
import uuid

from fastapi import APIRouter, UploadFile, HTTPException, Depends
from fastapi.params import File
from fastapi_another_jwt_auth import AuthJWT
from sqlalchemy.exc import SQLAlchemyError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from labstructanalyzer.configs.config import CONFIG_DIR, tool_conf
from labstructanalyzer.core.dependencies import get_template_service, get_report_service, get_answer_service
from labstructanalyzer.models.dto.modify_template import TemplateToModify
from labstructanalyzer.models.dto.report import MinimalReportInfoDto, AllReportsDto
from labstructanalyzer.models.dto.template import TemplateWithElementsDto, AllTemplatesDto, \
    TemplateMinimalProperties
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.course import Course
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.services.pylti1p3.cache import FastAPICacheDataStorage
from labstructanalyzer.services.pylti1p3.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.pylti1p3.request import FastAPIRequest
from labstructanalyzer.services.parser.docx import DocxParser
from labstructanalyzer.services.report import ReportService, ReportStatus
from labstructanalyzer.services.template import TemplateService
from labstructanalyzer.utils.rbac_decorator import roles_required

router = APIRouter()
template_prefix = "images\\template"


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
                    "example": {"detail": "Нет файла шаблона"}
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
                    "example": {"detail": "Произошла ошибка при сохранении данных, попробуйте еще раз"}
                }
            }
        },
    },
)
@roles_required(["teacher"])
async def parse_template(
        authorize: AuthJWT = Depends(),
        template: UploadFile = File(..., description="DOCX файл для обработки"),
        template_service: TemplateService = Depends(get_template_service)
):
    """
    Преобразовать шаблон из docx в json, применяя структуру.

    - **template**: Файл формата `.docx` для обработки.
    - Требуется роль **teacher**.
    """
    if not template:
        raise HTTPException(
            status_code=400,
            detail="Нет файла шаблона"
        )

    file_name_parts = os.path.splitext(os.path.basename(template.filename))

    if file_name_parts[1].lower() != ".docx":
        raise HTTPException(
            status_code=400,
            detail="Тип файла не поддерживается"
        )

    file_path = os.path.join(CONFIG_DIR, "structure.json")
    with open(file_path, 'r', encoding='utf-8') as file:
        data_dict = json.load(file)
    docx_parser = DocxParser(await template.read(), data_dict, template_prefix)
    template_components = docx_parser.get_structure_components()

    raw_jwt = authorize.get_raw_jwt()
    course_id = raw_jwt.get("course_id")
    user_id = raw_jwt.get("sub")

    try:
        template_model = await template_service.create(user_id, course_id, file_name_parts[0], template_components)
        return JSONResponse({"template_id": str(template_model.template_id)})
    except SQLAlchemyError:
        return JSONResponse({"detail": "Произошла ошибка при сохранении данных, попробуйте еще раз"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            "description": "Неавторизованный доступ.",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            }
        },
        403: {
            "description": "Доступ запрещен. Требуется роль преподавателя.",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Ошибка запроса. Шаблон не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Шаблон не найден"}
                }
            }
        },
        500: {
            "description": "Служба AGS недоступна со стороны LMS (не включена / прочие сбои LMS)",
            "content": {
                "application/json": {
                    "example": {"detail": "c"}
                }
            }
        },
        500: {
            "description": "Ошибка со стороны БД",
            "content": {
                "application/json": {
                    "example": {"detail": "Произошла ошибка при сохранении данных, попробуйте еще раз"}
                }
            }
        },
    },
)
@roles_required(["teacher"])
async def save_modified_template(
        request: Request,
        template_id: uuid.UUID,
        modified_template: TemplateToModify,
        authorize: AuthJWT = Depends(),
        template_service: TemplateService = Depends(get_template_service)
):
    try:
        template = await template_service.update(template_id, modified_template)

        if not modified_template.is_draft:
            launch_data_storage = FastAPICacheDataStorage(cache)
            message_launch = FastAPIMessageLaunch.from_cache(authorize.get_raw_jwt().get("launch_id"),
                                                             FastAPIRequest(request),
                                                             tool_conf,
                                                             launch_data_storage=launch_data_storage)
            ags_service = AgsService(message_launch)
            ags_service.create_lineitem(template)
        return JSONResponse({"detail": "Шаблон обновлен успешно"})

    except SQLAlchemyError:
        return JSONResponse({"detail": "Произошла ошибка при сохранении данных, попробуйте еще раз"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        }
    },
)
async def get_templates(request: Request,
                        authorize: AuthJWT = Depends(),
                        template_service: TemplateService = Depends(get_template_service)
                        ):
    authorize.jwt_required()
    raw_jwt = authorize.get_raw_jwt()
    course_id = raw_jwt.get("course_id")

    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(raw_jwt.get("launch_id"), FastAPIRequest(request), tool_conf,
                                                     launch_data_storage=launch_data_storage)

    course_name = Course(message_launch).get_name()

    user_roles = raw_jwt.get("roles")
    has_full_access = "teacher" in user_roles
    has_partial_access = "assistant" in user_roles
    with_reports = not (has_full_access or has_partial_access)

    templates_with_base_properties = await template_service.get_all_by_course(course_id, with_reports=with_reports)

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
        drafts_with_base_properties = await template_service.get_all_by_course(course_id, True)
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
            "description": "Неавторизованный доступ.",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            }
        },
        404: {
            "description": "Ошибка запроса. Шаблон не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Шаблон не найден"}
                }
            }
        },
        500: {
            "description": "Ошибка со стороны БД",
            "content": {
                "application/json": {
                    "example": {"detail": "Произошла ошибка при получении данных"}
                }
            }
        },
    },
)
async def get_template(
        template_id: uuid.UUID,
        authorize: AuthJWT = Depends(),
        template_service: TemplateService = Depends(get_template_service)
):
    authorize.jwt_required()
    try:
        template = await template_service.get_by_id(template_id)
        if template:
            elements = template_service.build_hierarchy(template.elements)

            roles = authorize.get_raw_jwt().get("roles")
            can_edit = "teacher" in roles
            can_grade = can_edit or "assistant" in roles
            return TemplateWithElementsDto(
                template_id=template_id,
                name=template.name,
                is_draft=template.is_draft,
                max_score=template.max_score,
                can_edit=can_edit,
                can_grade=can_grade,
                elements=elements
            )
        return JSONResponse({"detail": "Шаблон не найден"}, status_code=404)
    except SQLAlchemyError:
        return JSONResponse({"detail": "Произошла ошибка при получении данных"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            "description": "Неавторизованный доступ.",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            }
        },
        403: {
            "description": "Доступ запрещен. Требуется роль преподавателя.",
            "content": {
                "application/json": {
                    "example": {"detail": "Доступ запрещен"}
                }
            }
        },
        404: {
            "description": "Ошибка запроса. Шаблон не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Шаблон не найден"}
                }
            }
        },
        500: {
            "description": "Служба AGS недоступна со стороны LMS (не включена / прочие сбои LMS)",
            "content": {
                "application/json": {
                    "example": {"detail": "Нет доступа к службе оценок"}
                }
            }
        },
        500: {
            "description": "Ошибка со стороны БД",
            "content": {
                "application/json": {
                    "example": {"detail": "Произошла ошибка при удалении данных, попробуйте еще раз"}
                }
            }
        },
    },
)
@roles_required(["teacher"])
async def remove_template(
        request: Request,
        template_id: uuid.UUID,
        authorize: AuthJWT = Depends(),
        template_service: TemplateService = Depends(get_template_service)
):
    try:
        await template_service.delete(template_id)
        launch_data_storage = FastAPICacheDataStorage(cache)
        message_launch = FastAPIMessageLaunch.from_cache(authorize.get_raw_jwt().get("launch_id"),
                                                         FastAPIRequest(request),
                                                         tool_conf,
                                                         launch_data_storage=launch_data_storage)

        ags_service = AgsService(message_launch)
        ags_service.delete_lineitem(template_id)
        return JSONResponse({"detail": "Шаблон успешно удален"})


    except SQLAlchemyError:
        return JSONResponse({"detail": "Произошла ошибка при удалении данных"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            "description": "Ошибка запроса. Шаблон не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Шаблон не найден"}
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {"detail": "Ошибка при создании отчета"}
                }
            }
        }
    }
)
@roles_required(["student"])
async def create_report(
        template_id: uuid.UUID,
        authorize: AuthJWT = Depends(),
        report_service: ReportService = Depends(get_report_service),
        template_service: TemplateService = Depends(get_template_service),
        answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Создать отчет на основе данных из шаблона
    """
    user_id = authorize.get_jwt_subject()
    report_id = await report_service.create(template_id, user_id)
    template = await template_service.get_by_id(template_id)
    await answer_service.create_answers(template, report_id)

    return JSONResponse({"id": str(report_id)})


@router.get("/{template_id}/reports",
            tags=["Template", "Report"],
            summary="Получить все шаблоны по отчету"
            )
@roles_required(["teacher", "assistant"])
async def get_reports_by_template(
        template_id: uuid.UUID,
        request: Request,
        authorize: AuthJWT = Depends(),
        template_service: TemplateService = Depends(get_template_service)
):
    """
    Получает краткую информацию о всех доступных версиях отчетов всех обучающихся курса конкретного шаблона,
    доступных для отображения согласно статусу (отправлен на (повторную) проверку / проверен)
    """
    all_reports = await template_service.get_all_reports(template_id)
    template = await template_service.get_by_id(template_id)
    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(authorize.get_raw_jwt().get("launch_id"),
                                                     FastAPIRequest(request),
                                                     tool_conf,
                                                     launch_data_storage=launch_data_storage)
    nrps_service = NrpsService(message_launch)
    return AllReportsDto(
        template_name=template.name,
        max_score=template.max_score,
        reports=[
            MinimalReportInfoDto(
                report_id=report.report_id,
                date=report.updated_at,
                status=ReportStatus[report.status].value,
                author_name=nrps_service.get_user_name(report.author_id),
                score=report.score
            ) for report in all_reports
        ]
    )
