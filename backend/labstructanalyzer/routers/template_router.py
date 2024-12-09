import json
import os

from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.params import File
from starlette.responses import Response

from labstructanalyzer.configs.config import CONFIG_DIR
from labstructanalyzer.services.parser.docx import DocxParser
from labstructanalyzer.utils.file_utils import FileUtils
from labstructanalyzer.utils.rbac_decorator import roles_required

router = APIRouter(prefix="/template")
template_prefix = "images\\temp"


@router.post("")
@roles_required(["admin"])
async def parse_template(template: UploadFile = File(...)):
    """
    Преобразовать шаблон из docx в json, применяя структуру
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


@router.get("/image/{filename}")
@roles_required(["admin"])
async def get_temp_image(filename: str):
    """
    Получить изображение из шаблона.
    Внимание! Получить изображение можно только один раз!
    """
    try:
        image = FileUtils.get(template_prefix, filename)
        FileUtils.remove(template_prefix, filename)
        return Response(content=image, media_type="image/png")
    except IOError as error:
        return HTTPException(404, "Файл не найден")
