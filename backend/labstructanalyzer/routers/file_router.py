from fastapi import APIRouter, HTTPException
from starlette.responses import Response

from labstructanalyzer.routers.template_router import template_prefix
from labstructanalyzer.utils.file_utils import FileUtils
from labstructanalyzer.utils.rbac_decorator import roles_required

router = APIRouter()

@router.get("/images/temp/{filename}")
@roles_required(["teacher"])
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
