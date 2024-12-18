from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_another_jwt_auth import AuthJWT
from fastapi_another_jwt_auth.exceptions import AuthJWTException
from starlette.requests import Request
from pydantic import BaseModel

from labstructanalyzer.configs.config import tool_conf
from labstructanalyzer.models.UserCourseInfo import UserCourseInfo
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.services.lti.cache import FastAPICacheDataStorage
from labstructanalyzer.services.lti.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.lti.request import FastAPIRequest

router = APIRouter()


@router.post(
    "",
    tags=["User"],
    responses={
        200: {"model": UserCourseInfo},
        401: {
            "description": "Не авторизован или refresh токен истек",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
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
    description="""Получение полного имени, URL аватара и названия курса для аутентифицированного пользователя через данные LTI-запуска.

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
    try:
        authorize.jwt_required()
        raw_jwt = authorize.get_raw_jwt()
        user_id = raw_jwt.get("sub")

        launch_data_storage = FastAPICacheDataStorage(cache)
        message_launch = FastAPIMessageLaunch.from_cache(raw_jwt.get("launch_id"), FastAPIRequest(request), tool_conf,
                                                         launch_data_storage=launch_data_storage)

        lms_url = message_launch.get_iss()
        nrps = message_launch.get_nrps()
        course_name = nrps.get_context().get("title")
        avatar_url = f"{lms_url}/user/pix.php/{user_id}/f1.jpg"
        members = nrps.get_members()

        username = next((user.get('name') for user in members if str(user.get('user_id')) == str(user_id)), None)
        if not username:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        return UserCourseInfo(fullName=username, avatarUrl=avatar_url, courseName=course_name)

    except AuthJWTException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")
