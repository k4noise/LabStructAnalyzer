import json
import os
import uuid

from fastapi import APIRouter, UploadFile, HTTPException, Depends
from fastapi.params import File
from fastapi_another_jwt_auth import AuthJWT
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.responses import JSONResponse

from labstructanalyzer.configs.config import CONFIG_DIR
from labstructanalyzer.database import get_session
from labstructanalyzer.models.dto.template import TemplateDto
from labstructanalyzer.models.template import Template
from labstructanalyzer.models.template_element import TemplateElement
from labstructanalyzer.services.parser.docx import DocxParser
from labstructanalyzer.utils.rbac_decorator import roles_required

router = APIRouter()
template_prefix = "images\\temp"


@router.post(
    "",
    summary="Преобразовать шаблон из docx в json",
    description="Принимает файл формата `.docx`, применяет структуру и возвращает JSON-компоненты.",
    tags=["Template"],
    responses={
        200: {
            "description": "Успешное преобразование шаблона.",
            "content": {
                "application/json": {
                    "example": {"template_id": "c72869cb-8ac0-48b7-936f-370917e82b8e"}
                }
            }
        },
        400: {
            "description": "Ошибка запроса. Файл отсутствует или имеет неподдерживаемый формат.",
            "content": {
                "application/json": {
                    "example": {"detail": "Нет файла шаблона"}
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
    },
)
@roles_required(["teacher"])
async def parse_template(
        authorize: AuthJWT = Depends(),
        template: UploadFile = File(..., description="DOCX файл для обработки"),
        session: AsyncSession = Depends(get_session)
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

    template_model = Template(
        user_id=raw_jwt.get("sub"),
        course_id=course_id,
        name=file_name_parts[0],
        is_draft=True,
        elements=[TemplateElement(
            properties=template_element,
            element_type=template_element.get("type"),
            order=i + 1
        ) for i, template_element in enumerate(template_components)]
    )

    try:
        session.add(template_model)
        await session.commit()
        await session.refresh(template_model)
        return JSONResponse({"template_id": str(template_model.template_id)})
    except Exception as e:
        print(e)
        await session.rollback()


@router.get(
    "/{template_id}",
    response_model=TemplateDto,
    summary="Получить данные шаблона",
    description="Возвращает свойства шаблона и все дочерние элементы",
    tags=["Template"],
    responses={
        200: {
            "description": "Данные шаблона.",
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
    },
)
async def get_template(
        template_id: uuid.UUID,
        authorize: AuthJWT = Depends(),
        session: AsyncSession = Depends(get_session)
):
    authorize.jwt_required()
    try:
        template = await session.get(Template, template_id)
        if template:
            return template
        return JSONResponse({"detail": "Шаблон не найден"}, status_code=404)
    except Exception as e:
        print(e)
        await session.rollback()


