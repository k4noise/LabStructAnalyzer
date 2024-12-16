from fastapi import APIRouter, HTTPException
from starlette.responses import Response

from labstructanalyzer.routers.template_router import template_prefix
from labstructanalyzer.utils.file_utils import FileUtils

router = APIRouter()

@router.get("/images/temp/{filename}")
async def get_temp_image(filename: str):
    """
    Получить изображение из шаблона.
    """
    try:
        image = FileUtils.get(template_prefix, filename)
        return Response(content=image, media_type="image/png")
    except IOError as error:
        return HTTPException(404, "Файл не найден")
