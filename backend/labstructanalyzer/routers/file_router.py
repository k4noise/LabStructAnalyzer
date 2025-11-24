import os

from fastapi import APIRouter, File, UploadFile, Depends
from starlette.responses import Response, JSONResponse

from labstructanalyzer.configs.config import IMAGE_PREFIX, USER_IMAGE_PREFIX
from labstructanalyzer.core.dependencies import get_file_storage
from labstructanalyzer.utils.files.hybrid_storage import HybridStorage

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
async def get_temp_image(
        file_key: str,
        file_storage: HybridStorage = Depends(get_file_storage)
):
    """Получить изображение из шаблона"""
    image = file_storage.get(os.path.join(IMAGE_PREFIX, file_key))
    return Response(content=image, media_type="image/png")


@router.post(
    "/upload",
    tags=["File"],
    summary="Загрузить пользовательское изображение",
    description="Сохраняет изображение",
    responses={
        200: {
            "description": "Изображение сохранено",
            "content": {
                "application/json": {
                    "example": {
                        "key": "/key/to/file"
                    }
                }
            }
        },
        500: {
            "description": "Не получилось сохранить изображение",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Ошибка файловой системы"
                    }
                }
            }
        }
    })
async def save_image(
        file: UploadFile = File(...),
        file_storage: HybridStorage = Depends(get_file_storage)
):
    """Сохранить пользовательское изображение"""
    file_data = await file.read()
    extension = file.filename.split(".")[-1] if "." in file.filename else "png"

    file_key = file_storage.save(
        path=USER_IMAGE_PREFIX,
        file_data=file_data,
        extension=extension
    )

    return JSONResponse(content={"url": file_key})


@router.delete(
    "/{file_key:path}",
    tags=["File"],
    summary="Удалить изображение",
    description="Удаляет изображение по ключу файла",
    responses={
        200: {
            "description": "Изображение удалено"
        }
    })
async def delete_image(
        file_key: str,
        file_storage: HybridStorage = Depends(get_file_storage)
):
    """Удалить изображение по ключу"""
    file_storage.delete(file_key)
    return Response(status_code=200)
