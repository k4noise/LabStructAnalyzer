from fastapi import APIRouter, Depends
from fastapi_another_jwt_auth import AuthJWT
from starlette.responses import JSONResponse

from labstructanalyzer.configs.config import JWT_ACCESS_TOKEN_LIFETIME
from labstructanalyzer.services.lti.jwt import JWT

router = APIRouter()


@router.post(
    "/refresh", tags=["JWT"],
    summary="Обновление токена доступа JWT",
    description="Позволяет обновить только access токен при наличии действительного refresh токена",
    responses={
        200: {
            "description": "Токен доступа успешно обновлен",
        },
        401: {
            "description": "Не авторизован или refresh токен истек",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            },
        }
    }
)
async def refresh_access_token(authorize: AuthJWT = Depends()):
    """
    Обновить токен доступа

    Args:
        authorize: Объект создания и проверки JWT токенов

    Returns:
        JSONResponse: Сообщение о результате операции
    """
    authorize.jwt_refresh_token_required()

    current_user = authorize.get_jwt_subject()
    raw_jwt = authorize.get_raw_jwt()
    user_claims = JWT().create_user_claims_at_jwt_object(raw_jwt)

    new_access_token = authorize.create_access_token(subject=current_user, user_claims=user_claims)
    authorize.set_access_cookies(new_access_token, max_age=JWT_ACCESS_TOKEN_LIFETIME)


@router.delete(
    "/logout", tags=["JWT"],
    summary="Выход из аккаунта",
    description="Удаляет JWT токены из куки, осуществляя выход пользователя из аккаунта",
    responses={
        200: {
            "description": "Успешный выход из аккаунта"
        }
    }
)
async def logout(authorize: AuthJWT = Depends()):
    """
    Выполнить выход из аккаунта, удалив все связанные JWT токены.
    Если кук нет, то ничего не произойдет.

    Args:
        authorize (AuthJWT): Объект для чтения и удаления JWT токенов.

    Returns:
        dict: Сообщение о результате операции.
    """
    authorize.unset_jwt_cookies()
