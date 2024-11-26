import os

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi_another_jwt_auth import AuthJWT
from lti import ToolProvider

from labstructanalyzer.config import Settings
from labstructanalyzer.utils.lti_validator import LTIRequestValidator

settings = Settings()
validator = LTIRequestValidator(settings)

router = APIRouter()


@router.post("/lti")
async def login_with_lti_credential(request: Request, authorize: AuthJWT = Depends()):
    """
    Вход через LTI-провайдера
    """
    form = await request.form()
    tool_provider = ToolProvider.from_unpacked_request(
        os.getenv("LTI_SECRET_KEY"),
        form,
        str(request.url),
        request.headers
    )

    if not tool_provider.is_valid_request(validator):
        raise HTTPException(status_code=401, detail="Неверный запрос LTI")

    user_id = form.get('user_id')
    user_roles = form.get('roles')

    access_token = authorize.create_access_token(subject=user_id, user_claims={"roles": user_roles})
    refresh_token = authorize.create_refresh_token(subject=user_id)
    response = RedirectResponse(url=os.getenv("FRONTEND_URL"), status_code=302)
    response.set_cookie(key="access_token", value=access_token)
    response.set_cookie(key="refresh_token", value=refresh_token, secure=True)
    return response