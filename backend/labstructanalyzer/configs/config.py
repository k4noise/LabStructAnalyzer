import os

from fastapi_another_jwt_auth import AuthJWT
from pydantic import BaseModel
from pylti1p3.tool_config import ToolConfJsonFile

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PROJECT_DIR = os.path.dirname(os.path.dirname(CONFIG_DIR))
LTI_CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'lti_config.json')
TOOL_CONF = ToolConfJsonFile(LTI_CONFIG_FILE_PATH)

FILES_STORAGE_DIR = BASE_PROJECT_DIR
ONNX_MODEL_DIR = f"{BASE_PROJECT_DIR}/labstructanalyzer/assets/rubert-tiny2"
GENERATE_MODEL_DIR = f"{BASE_PROJECT_DIR}/labstructanalyzer/assets/rut5-base-multitask"

IMAGE_PREFIX = "images"
TEMPLATE_IMAGE_PREFIX = f"{IMAGE_PREFIX}/template"
USER_IMAGE_PREFIX = f"{IMAGE_PREFIX}/content"
JWT_ACCESS_TOKEN_LIFETIME = 15 * 60  # 15 минут


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
