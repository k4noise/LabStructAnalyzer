from fastapi import APIRouter, Depends
from fastapi_another_jwt_auth import AuthJWT

from pydantic import BaseModel
from labstructanalyzer.configs.config import User

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


@router.post("/token", response_model=TokenResponse)
async def get_jwt_pair(user: User, authorize: AuthJWT = Depends()):
    """
    Выдать пользователю связку токенов после проверки LTI-запроса

    Args:
        user: Данные пользователя (id, role) из Moodle
        authorize: Объект для создания JWT токенов
    """
    access_token = authorize.create_access_token(subject=user.id, user_claims={"role": user.role})
    refresh_token = authorize.create_refresh_token(subject=user.id, user_claims={"role": user.role})
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/access", response_model=TokenResponse)
async def refresh_access_token(authorize: AuthJWT = Depends()):
    """
    Обновить только access токен

    Args:
        authorize: Объект для создания JWT токенов
    """
    authorize.jwt_refresh_token_required()

    current_user = authorize.get_jwt_subject()
    role = authorize.get_raw_jwt()["role"]

    new_access_token = authorize.create_access_token(subject=current_user, user_claims={"role": role})
    return {"access_token": new_access_token}
