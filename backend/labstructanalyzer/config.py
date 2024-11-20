import os

from fastapi.security import OAuth2PasswordBearer
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel


@AuthJWT.load_config
def get_config():
    return Settings()


class Settings(BaseModel):
    """
    Настройки JWT
    """
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: set = {"access", "refresh"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    """
    Базовая модель пользователя
    """
    id: str
    role: str
