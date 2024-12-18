import json
import os

from fastapi import APIRouter, UploadFile, HTTPException, Depends
from fastapi.params import File
from fastapi_another_jwt_auth import AuthJWT

from labstructanalyzer.configs.config import CONFIG_DIR
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
        template: UploadFile = File(..., description="DOCX файл для обработки")
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

    if not template.filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail="Тип файла не поддерживается"
        )

    file_path = os.path.join(CONFIG_DIR, "structure.json")
    with open(file_path, 'r', encoding='utf-8') as file:
        data_dict = json.load(file)
    docx_parser = DocxParser(await template.read(), data_dict, template_prefix)
    return docx_parser.get_structure_components()
