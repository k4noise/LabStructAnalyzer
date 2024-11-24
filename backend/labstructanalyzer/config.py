import os

from fastapi_another_jwt_auth import AuthJWT
from pydantic import BaseModel


class Settings(BaseModel):
    """
    Настройки JWT
    """
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: set = {"access", "refresh"}

@AuthJWT.load_config
def get_config():
    return Settings()


class User(BaseModel):
    """
    Базовая модель пользователя
    """
    id: str
    role: str
