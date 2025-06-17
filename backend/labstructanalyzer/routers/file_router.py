import os

from fastapi import APIRouter, File, UploadFile, Depends
from starlette.responses import Response, JSONResponse

from labstructanalyzer.configs.config import IMAGE_PREFIX, USER_IMAGE_PREFIX
from labstructanalyzer.core.dependencies import get_chain_storage
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
async def get_temp_image(
        file_key: str,
        chain_storage: ChainStorage = Depends(get_chain_storage)
):
    """
    Получить изображение из шаблона
    """
    image = chain_storage.get(os.path.join(IMAGE_PREFIX, file_key))
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
        chain_storage: ChainStorage = Depends(get_chain_storage)
):
    """
    Сохранить пользовательское изображение
    """
    file_data = await file.read()
    extension = file.filename.split(".")[-1] if "." in file.filename else "png"

    file_key = chain_storage.save(
        save_dir=USER_IMAGE_PREFIX,
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
        chain_storage: ChainStorage = Depends(get_chain_storage)
):
    """
    Удалить изображение по ключу
    """
    chain_storage.remove(file_key)
    return Response(status_code=200)
