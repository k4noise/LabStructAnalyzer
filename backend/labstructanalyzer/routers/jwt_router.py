from fastapi import APIRouter, Depends
from fastapi_another_jwt_auth import AuthJWT

from labstructanalyzer.configs.config import User, JWT_ACCESS_TOKEN_LIFETIME

router = APIRouter()


@router.post("/token")
async def get_jwt_pair(user: User, authorize: AuthJWT = Depends()):
    """
    Выдать пользователю связку токенов после проверки LTI-запроса

    Args:
        user: Данные пользователя (id, role) из Moodle
        authorize: Объект для создания JWT токенов
    """
    access_token = authorize.create_access_token(subject=user.id, user_claims={"role": user.role})
    refresh_token = authorize.create_refresh_token(subject=user.id, user_claims={"role": user.role})
    authorize.set_access_cookies(access_token)
    authorize.set_refresh_cookies(refresh_token)
    return {"message": "Установлены новые токены"}


@router.post("/refresh")
async def refresh_access_token(authorize: AuthJWT = Depends()):
    """
    Обновить только access токен

    Args:
        authorize: Объект для создания JWT токенов
    """
    authorize.jwt_refresh_token_required()

    current_user = authorize.get_jwt_subject()
    role = authorize.get_raw_jwt().get("role")

    new_access_token = authorize.create_access_token(subject=current_user, user_claims={"role": role})
    authorize.set_access_cookies(new_access_token, max_age=JWT_ACCESS_TOKEN_LIFETIME)
    return {"message": "Обновлен токен доступа"}


@router.delete("/logout")
async def logout(authorize: AuthJWT = Depends()):
    """
    Произвести выход из аккаунта

    Args:
        authorize: Объект для чтения/удаления JWT токенов
    """
    authorize.jwt_required()

    authorize.unset_jwt_cookies()
    return {"message": "Произведен выход из аккаунта"}
