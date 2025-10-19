from fastapi import HTTPException
from starlette import status
from starlette.requests import Request

from labstructanalyzer.core.logger import GlobalLogger

logger = GlobalLogger().get_logger(__name__)


async def invalid_oidc_state(request: Request, exception: Exception):
    logger.warning("Отсутствуют необходимые для OIDC параметры", request, exception)
    raise HTTPException(detail='Вход не выполнен, попробуйте ещё раз', status_code=status.HTTP_400_BAD_REQUEST)


async def invalid_jwt_state(request: Request, exception: Exception):
    logger.info(
        "Ошибка JWT. " + exception.message + "\nУстановленные cookie (keys only): " + ', '.join(request.cookies.keys()))
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")


async def invalid_lti_state(request: Request, exception: Exception):
    logger.error("Ошибка LTI", request, exception)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Ошибка внешнего инструмента")


async def no_lis_service_access(request: Request, exception: Exception):
    logger.error("Нет доступа к сервису LTI LIS", request, exception)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Нет доступа к сервисам LIS")


async def access_denied(request: Request, exception: Exception):
    logger.warning("Нет доступа к ресурсу", request, exception)
    # Сокрытие деталей реализации и ничего более, 404 - не ошибка.
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено")


async def invalid_action(request: Request, exception: Exception):
    logger.error("Не выполнено", request, exception)
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Действие невозможно")


async def parser_error(request: Request, exception: Exception):
    logger.error("Ошибка сохранения шаблона", request, exception)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="")


async def os_error_handler(request: Request, exception: Exception):
    if isinstance(exception, FileNotFoundError):
        logger.error(f"Файл не найден", request, exception)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден")

    logger.error(f"Ошибка файловой системы", request, exception)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка доступа к файлу")


async def database_error(request: Request, exception: Exception):
    logger.error("Ошибка базы данных", request, exception)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка доступа к данным")


async def no_entity_error(request: Request, exception: Exception):
    logger.warning("Сущность не найдена", request, exception)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено")
