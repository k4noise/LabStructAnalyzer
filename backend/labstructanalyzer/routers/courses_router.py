from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi_another_jwt_auth import AuthJWT
from fastapi_another_jwt_auth.exceptions import AuthJWTException
from pylti1p3.exception import LtiException
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from labstructanalyzer.configs.config import tool_conf
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.services.lti.cache import FastAPICacheDataStorage
from labstructanalyzer.services.lti.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.lti.request import FastAPIRequest

router = APIRouter()


@router.get(
    "/current",
    tags=["Course"],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"name": "Test Course"}
                }
            },
        },
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
    summary="Получение информации о курсе",
    description="""Получение названия курса для аутентифицированного пользователя.
    
    Этот эндпоинт требует действительного JWT-токена, который должен содержать информацию о LTI-запуске.
    Он использует контекст LTI для получения пользовательских данных из системы управления обучением (LMS).
    """
)
async def get_current_course_name(request: Request, authorize: AuthJWT = Depends()):
    try:
        authorize.jwt_required()
        raw_jwt = authorize.get_raw_jwt()

        launch_data_storage = FastAPICacheDataStorage(cache)
        message_launch = FastAPIMessageLaunch.from_cache(raw_jwt.get("launch_id"), FastAPIRequest(request), tool_conf,
                                                         launch_data_storage=launch_data_storage)
        course_name = message_launch.get_nrps() \
            .get_context() \
            .get("title")

        return JSONResponse({"name": course_name})

    except AuthJWTException or LtiException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")

