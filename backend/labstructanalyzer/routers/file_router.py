from fastapi import APIRouter
from starlette.responses import Response

from labstructanalyzer.configs.config import TEMPLATE_IMAGE_PREFIX
from labstructanalyzer.utils.file_utils import FileUtils

router = APIRouter(
    tags=["File"],
    prefix="/images"
)


@router.get(
    "/template/{filename}",
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
        },
        500: {
            "description": "Ошибка доступа к файлу",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Ошибка доступа к файлу"
                    }
                }
            }
        }
    })
async def get_temp_image(filename: str):
    """
    Получить изображение из шаблона
    """
    image = FileUtils.get(TEMPLATE_IMAGE_PREFIX, filename)
    return Response(content=image, media_type="image/png")
