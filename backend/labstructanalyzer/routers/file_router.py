from fastapi import APIRouter, HTTPException
from starlette import status
from starlette.responses import Response

from labstructanalyzer.routers.template_router import template_prefix
from labstructanalyzer.utils.file_utils import FileUtils

router = APIRouter(
    tags=["File"],
    prefix="/images"
)


@router.get(
    "/temp/{filename}",
    summary="Получить изображение из шаблона",
    description="Возвращает изображение из шаблона по имени файла",
    responses={
        200: {
            "description": "Изображение из шаблона",
            "content": {
                "image/png": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        404: {
            "description": "Файл не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Файл не найден"
                    }
                }
            }
        }
    })
async def get_temp_image(filename: str):
    """
    Получить изображение из шаблона.
    """
    try:
        image = FileUtils.get(template_prefix, filename)
        return Response(content=image, media_type="image/png")
    except IOError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не найден")
