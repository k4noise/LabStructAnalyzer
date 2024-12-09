import os

from fastapi import APIRouter, Request
from fastapi.params import Depends
from fastapi_another_jwt_auth import AuthJWT
from fastapi_cache.backends.inmemory import InMemoryBackend
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.oidc_login import OIDCException
from starlette.responses import RedirectResponse, Response, JSONResponse

from labstructanalyzer.configs.config import LTI_CONFIG_FILE_PATH
from labstructanalyzer.services.lti.cache import FastAPICacheDataStorage
from labstructanalyzer.services.lti.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.lti.oidc_login import FastAPIOIDCLogin
from labstructanalyzer.services.lti.request import FastAPIRequest
from labstructanalyzer.services.lti.roles import LTIRoles

router = APIRouter(prefix="/lti")
cache = InMemoryBackend()


@router.get("/login")
@router.post("/login")
async def login(request: Request):
    """
    Обрабатывает аутентификацию через OIDCv3 по LTI 1.3.

    Args:
        request: Запрос с данными поставщика для начала аутентификации

    Returns:
        - Перенаправление на службу аутентификации поставщика, если аутентификация успешна
        - Ответ с 401, если аутентификация не удалась
    """
    tool_conf = ToolConfJsonFile(LTI_CONFIG_FILE_PATH)
    launch_data_storage = FastAPICacheDataStorage(cache)
    request_obj = FastAPIRequest(request)
    await request_obj.parse_request()
    target_link_uri = request_obj.get_param("target_link_uri")
    if not target_link_uri:
        return Response('Нет параметра "target_link_uri"', 400)

    oidc_login = FastAPIOIDCLogin(request_obj, tool_conf, launch_data_storage=launch_data_storage)
    try:
        return oidc_login \
            .disable_check_cookies() \
            .redirect(target_link_uri)
    except OIDCException:
        return Response('Error doing OIDC login', 403)


@router.post("/launch")
async def launch(request: Request, authorize: AuthJWT = Depends()):
    """
    Запускает систему через LTI после успешной аутентификации.

    Args:
        request: Запрос, содержащий id_token от потребителя

    Returns:
        Перенаправление на фронтенд системы
    """
    tool_conf = ToolConfJsonFile(LTI_CONFIG_FILE_PATH)
    request_obj = FastAPIRequest(request)
    await request_obj.parse_request()
    launch_data_storage = FastAPICacheDataStorage(cache)
    message_launch = FastAPIMessageLaunch(request_obj, tool_conf, launch_data_storage=launch_data_storage)
    roles = LTIRoles(message_launch)
    role = roles.get_role()
    user_id = message_launch.get_launch_data().get('sub')

    access_token = authorize.create_access_token(subject=user_id, user_claims={"role": role})
    refresh_token = authorize.create_refresh_token(subject=user_id)
    response = RedirectResponse(url="http://127.0.0.1:5173/", status_code=302)
    response.set_cookie(key="access_token", value=access_token, samesite='none', secure=True)
    response.set_cookie(key="refresh_token", value=refresh_token, samesite='none', secure=True, httponly=True)
    return response


@router.get("/jwks")
async def jwks():
    """
    Предоставляет открытые ключи для верификации LTI tool.

    Returns:
        dict: JSON Web Key Set из открытого ключа
    """
    tool_conf = ToolConfJsonFile(LTI_CONFIG_FILE_PATH)
    return JSONResponse(tool_conf.get_jwks())
