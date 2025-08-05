import os
from urllib.parse import urljoin

from fastapi import APIRouter, Request
from fastapi.params import Depends, Query
from fastapi_another_jwt_auth import AuthJWT
from starlette.responses import RedirectResponse, JSONResponse

from labstructanalyzer.configs.config import JWT_ACCESS_TOKEN_LIFETIME, TOOL_CONF
from labstructanalyzer.services.lti.jwt import JwtClaimService
from labstructanalyzer.services.pylti1p3.cache import FastAPICacheDataStorage
from labstructanalyzer.services.pylti1p3.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.pylti1p3.oidc_login import FastAPIOIDCLogin
from labstructanalyzer.services.pylti1p3.request import FastAPIRequest
from labstructanalyzer.utils.ttl_cache import TTLCache

router = APIRouter()
cache = TTLCache()


@router.get("/login", tags=["LTI"], summary="Начало входа LTI 1.3",
            response_description="Перенаправляет на провайдера LTI",
            responses={
                500: {"description": "Отсутствуют необходимые для OIDC параметры",
                      "content": {
                          "application/json": {
                              "example": {"detail": 'Вход не выполнен, попробуйте ещё раз'}
                          }
                      }
                      }
            })
@router.post("/login", tags=["LTI"], summary="Начало входа LTI 1.3",
             response_description="Перенаправляет на провайдера LTI",
             responses={
                 500: {"description": "Отсутствуют необходимые для OIDC параметры",
                       "content": {
                           "application/json": {
                               "example": {"detail": 'Вход не выполнен, попробуйте ещё раз'}
                           }
                       }
                       }
             })
async def login(
        request: Request,
        target_link_uri: str = Query(None,
                                     description="URI целевой ссылки для перенаправления после успешной аутентификации."),
):
    """
    Обрабатывает аутентификацию LTI 1.3 через OIDC.

    Args:
        request: Запрос, содержащий данные провайдера для начала аутентификации
        target_link_uri: URI целевой ссылки для перенаправления после успешной аутентификации

    Returns:
        Перенаправляет на сервис аутентификации провайдера
    """
    launch_data_storage = FastAPICacheDataStorage(cache)
    fastapi_request = FastAPIRequest(request)
    await fastapi_request.parse_request()
    target_link_uri = target_link_uri or fastapi_request.get_param("target_link_uri")

    oidc_login = FastAPIOIDCLogin(fastapi_request, TOOL_CONF, launch_data_storage=launch_data_storage)
    return oidc_login \
        .disable_check_cookies() \
        .redirect(target_link_uri)


@router.post("/launch", tags=["LTI"], summary="Запуск LTI",
             status_code=302,
             response_description="Перенаправляет на фронтенд после успешного запуска",
             responses={
                 500: {"description": "Ошибка LTI регистрации",
                       "content": {
                           "application/json": {
                               "example": {"detail": 'Ошибка внешнего инструмента'}
                           }
                       }
                       }
             })
async def launch(request: Request, authorize: AuthJWT = Depends()):
    """
    Запускает систему через LTI после успешной аутентификации

    Args:
        request: Запрос, содержащий id_token от потребителя
        authorize: Объект для управления JWT токенами

    Returns:
        Перенаправляет на фронтенд системы
    """
    request_obj = FastAPIRequest(request)
    await request_obj.parse_request()
    launch_data_storage = FastAPICacheDataStorage(cache)

    message_launch = FastAPIMessageLaunch(request_obj, TOOL_CONF, launch_data_storage=launch_data_storage)
    message_launch.validate_registration()

    user_id = message_launch.get_launch_data().get('sub')
    user_claims = JwtClaimService().create_user_claims_at_message_launch(message_launch)

    access_token = authorize.create_access_token(subject=user_id, user_claims=user_claims)
    refresh_token = authorize.create_refresh_token(subject=user_id, user_claims=user_claims)

    base_url = urljoin(os.getenv('FRONTEND_URL'), '/templates')
    response = RedirectResponse(url=base_url, status_code=302)
    authorize.set_access_cookies(access_token, response=response, max_age=JWT_ACCESS_TOKEN_LIFETIME)
    authorize.set_refresh_cookies(refresh_token, response=response, max_age=0)
    return response


@router.get("/jwks", tags=["LTI"], summary="Получение набора ключей JWKS",
            response_description="Возвращает публичный ключ",
            responses={
                200: {
                    "content": {
                        "application/json": {
                            "example": {
                                "keys": [
                                    {
                                        "e": "AQAB",
                                        "kid": "3ZfsqQvI4ZMBKXAZikcKxtc77i8g8Z3U_o3h53_0sYo",
                                        "kty": "RSA",
                                        "n": "y208DIIk64lJsOni1JXR4Gz0zM92YQsXBfv21w97erUEFRHsjIuZCyVApQ1JAe5oSU-Y6mAR_hXjYYOeoxbRafAJik50njs8V80UEGULtHnzWZSCfWKiB-9SmQ_a4xWg56GfX8VfFatQmmrA1Ac6t7JPcHm5Bo1icuFFxJfSXTrwpC4RLWtAKmz1FkSrxfHL7cB9JvqjHfkQcGrpgz8AefRedIxF-eXwEYRflMelpnnUQfQwI4ZullFkAPpVKjGDnMBewkuljoNzlC7Bkw1VAO39wGJzuUbWYmOc7bHlCY-jv6e79bIbTzf6iuo9aIgGP6XrzwZBR_OkszVFqqb1m2UMjUpcm2EAtaiDP6CAd-9z8Ol0sRm63Tve6QHy8ii8IuZ-AWwYdaq8MKtk48qg030PhJvHMscCtG_ub6kr-HrElYTw8HikY_ZlxzeWM6Ry0Mh2XPsRULmt-WR-9Fz07xugrYlk13llQ-cUzQssIGxXvb45_-Ns6MXnlHVHjpWP33vB3q1dqRdS93aZOPzkMmEAl-6LpmpMENVJ0Izen9ODK59enht9Bxev2U3U2Lb939oiSSLVbc_UcubjcV9Iwwwk1yI1LJbAe6IswlNR4-uvYnada-RDHCl1-Drvfm20fh_4JvoxQfogsJedrjCk-6jwyxY-yKyLSvq6lfFOHj8",
                                        "alg": "RS256",
                                        "use": "sig"
                                    }
                                ]
                            }
                        }
                    }
                }
            })
async def jwks():
    """
    Предоставляет публичные ключи для верификации LTI инструмента.

    Returns:
        JSON Web Key Set публичного ключа.
    """
    return JSONResponse(TOOL_CONF.get_jwks())
