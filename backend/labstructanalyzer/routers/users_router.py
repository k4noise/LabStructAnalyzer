from fastapi import APIRouter, Depends
from starlette.requests import Request

from labstructanalyzer.configs.config import TOOL_CONF
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.core.dependencies import get_user

from labstructanalyzer.models.user_info import UserInfoDto
from labstructanalyzer.models.user_model import User as UserModel
from labstructanalyzer.services.lti.nrps import NrpsService

from labstructanalyzer.services.pylti1p3.cache import FastAPICacheDataStorage
from labstructanalyzer.services.pylti1p3.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.pylti1p3.request import FastAPIRequest

router = APIRouter()


@router.get(
    "/me",
    tags=["User"],
    responses={
        200: {"model": UserInfoDto},
        401: {
            "description": "Не авторизован или refresh токен истек",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            },
        },
        403: {
            "description": "Не авторизован или refresh токен истек",
            "content": {
                "application/json": {
                    "example": {"detail": "Ошибка внешнего инструмента, необходим повторный вход через LMS"}
                }
            },
        },
    },
    summary="Получение информации о пользователе и курсе",
    description="""Получение имени (ФИО, имени и фамилии отдельно), URL аватара и роли для аутентифицированного пользователя через данные LTI-запуска.

    Этот эндпоинт требует действительного JWT-токена, который должен содержать информацию о LTI-запуске.
    Он использует контекст LTI для получения пользовательских данных из системы управления обучением (LMS).
    """
)
async def get_user_data(request: Request, user: UserModel = Depends(get_user)):
    """
    Получает и возвращает данные пользователя из контекста LTI запуска

    Args:
        request: Объект запроса FastAPI для доступа к данным запроса
        user: Параметры пользователя
    """

    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(user.launch_id, FastAPIRequest(request), TOOL_CONF,
                                                     launch_data_storage=launch_data_storage)

    user_data = NrpsService(message_launch)
    return UserInfoDto(
        full_name=user_data.get_current_full_name()
    )
