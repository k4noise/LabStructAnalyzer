from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi_jwt_auth import AuthJWT
from lti import ToolProvider
from oauthlib.oauth1 import RequestValidator

from labstructanalyzer.config import get_config

validator = RequestValidator()

router = APIRouter()

@router.post("/lti_login")
async def login_with_lti_credential(request: Request, authorize: AuthJWT = Depends()):
    """

    """
    settings = get_config()
    tool_provider = ToolProvider.from_unpacked_request(
        settings.lti_consumer_secret,
        request.json(),
        settings.lti_endpoint_url,
        request.headers
    )

    if not tool_provider.is_valid_request(validator):
        raise HTTPException(status_code=401, detail="Неверный запрос LTI")

    user_id = tool_provider.get_user_id()
    user_roles = tool_provider.get_roles()

    access_token = authorize.create_access_token(subject=user_id, user_claims={"roles": user_roles})
    refresh_token = authorize.create_refresh_token(subject=user_id)
    return {"access_token": access_token, "refresh_token": refresh_token}