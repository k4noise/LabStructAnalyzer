

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi_another_jwt_auth import AuthJWT
from fastapi_another_jwt_auth.exceptions import AuthJWTException
from starlette.responses import JSONResponse, Response

from labstructanalyzer.configs.config import JWT_ACCESS_TOKEN_LIFETIME

router = APIRouter()


@router.post(
    "/refresh", tags=["JWT"],
    summary="Обновление токена доступа JWT",
    description="Позволяет обновить только access токен при наличии действительного refresh токена",
    responses={
        200: {
            "description": "Токен доступа успешно обновлен",
            "content": {
                "application/json": {
                    "example": {"detail": "Обновлен токен доступа"}
                }
            },
        },
        401: {
            "description": "Не авторизован или refresh токен истек",
            "content": {
                "application/json": {
                    "example": {"detail": "Не авторизован"}
                }
            },
        },
    },
)
async def refresh_access_token(authorize: AuthJWT = Depends()):
    """
    Обновить токен доступа

    Args:
        authorize: Объект создания и проверки JWT токенов

    Returns:
        JSONResponse: Сообщение о результате операции
    """
    try:
        authorize.jwt_refresh_token_required()

        current_user = authorize.get_jwt_subject()
        raw_jwt = authorize.get_raw_jwt()
        role = raw_jwt.get("role")
        launch_id = raw_jwt.get("launch_id")
        course_id = raw_jwt.get("course_id")

        new_access_token = authorize.create_access_token(
            subject=current_user,
            user_claims={"role": role, "launch_id": launch_id, "course_id": course_id},
        )
        response = JSONResponse({"detail": "Обновлен токен доступа"})
        authorize.set_access_cookies(new_access_token, max_age=JWT_ACCESS_TOKEN_LIFETIME, response=response)
        return response
    except AuthJWTException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")


@router.delete(
    "/logout", tags=["JWT"],
    summary="Выход из аккаунта",
    description="Удаляет JWT токены из куки, осуществляя выход пользователя из аккаунта",
    responses={
        200: {
            "description": "Успешный выход из аккаунта",
            "content": {
                "application/json": {
                    "example": {"detail": "Произведен выход из аккаунта"}
                }
            },
        }
    },
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
    try:
        authorize.unset_jwt_cookies()
        return JSONResponse({"detail": "Произведен выход из аккаунта"})
    except AuthJWTException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")
