import os

from fastapi_another_jwt_auth import AuthJWT
from pydantic import BaseModel

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
LTI_CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'lti_config.json')

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
