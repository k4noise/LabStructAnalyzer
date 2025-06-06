import os

from fastapi import APIRouter
from starlette.responses import Response

from labstructanalyzer.configs.config import IMAGE_PREFIX
from labstructanalyzer.utils.files.chain_storage import ChainStorage

router = APIRouter()


@router.get(
    "/{file_key:path}",
    tags=["File"],
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
async def get_temp_image(file_key: str):
    """
    Получить изображение из шаблона
    """
    image = ChainStorage.get_default().get(os.path.join(IMAGE_PREFIX, file_key))
    
    return Response(content=image, media_type="image/png")
