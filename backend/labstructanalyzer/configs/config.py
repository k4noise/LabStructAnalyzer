import os

from fastapi_another_jwt_auth import AuthJWT
from pydantic import BaseModel
from pylti1p3.tool_config import ToolConfJsonFile

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
LTI_CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'lti_config.json')
tool_conf = ToolConfJsonFile(LTI_CONFIG_FILE_PATH)


JWT_ACCESS_TOKEN_LIFETIME = 15 * 60     # 15 минут


class Settings(BaseModel):
    """
    Переопределение настроек JWT Auth
    """
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    authjwt_token_location: set = {"cookies"}
    authjwt_cookie_csrf_protect: bool = False
    authjwt_access_token_expires: int = JWT_ACCESS_TOKEN_LIFETIME

@AuthJWT.load_config
def get_config():
    return Settings()


class User(BaseModel):
    """
    Базовая модель пользователя
    """
    id: str
    role: str
