from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_another_jwt_auth import AuthJWT
from starlette.requests import Request

from labstructanalyzer.configs.config import tool_conf
from labstructanalyzer.models.user_info import UserInfo
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.services.lti.cache import FastAPICacheDataStorage
from labstructanalyzer.services.lti.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.lti.request import FastAPIRequest

router = APIRouter()


@router.get(
    "/me",
    tags=["User"],
    responses={
        200: {"model": UserInfo},
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
        404: {
            "description": "Пользователь не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Пользователь не найден"}
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
async def get_user_data(request: Request, authorize: AuthJWT = Depends()):
    """
    Получает и возвращает данные пользователя из контекста LTI запуска.

    Args:
        request: Объект запроса FastAPI для доступа к данным запроса.
        authorize: Dependency для проверки JWT токена.
    """

    authorize.jwt_required()
    raw_jwt = authorize.get_raw_jwt()
    user_id = raw_jwt.get("sub")

    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch.from_cache(raw_jwt.get("launch_id"), FastAPIRequest(request), tool_conf,
                                                     launch_data_storage=launch_data_storage)

    lms_url = message_launch.get_iss()
    avatar_url = f"{lms_url}/user/pix.php/{user_id}/f1.jpg"
    members = message_launch.get_nrps().get_members()

    current_user = next((user for user in members if str(user.get('user_id')) == str(user_id)), None)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    return UserInfo(
        fullName=current_user.get("name"),
        name=current_user.get("given_name"),
        surname=current_user.get("family_name"),
        role=raw_jwt.get("role"),
        avatarUrl=avatar_url
    )
