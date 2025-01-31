from functools import wraps
from typing import List, Callable

from fastapi import HTTPException
from fastapi_another_jwt_auth import AuthJWT
from fastapi_another_jwt_auth.exceptions import AuthJWTException
from starlette import status


def roles_required(roles: List[str]) -> Callable:
    """
    Декоратор упрощенного RBAC.
    Для применения декоратора необходимо получить объект AuthJWT через Depends в самом роуте
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Callable:
            authorize: AuthJWT = kwargs.get('authorize', None)
            if not authorize:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")
            try:
                authorize.jwt_required()
                user_roles = authorize.get_raw_jwt().get("roles")
                if not any(item in roles for item in user_roles):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещён")
                return await func(*args, **kwargs)
            except AuthJWTException as exception:
                raise HTTPException(status_code=exception.status_code, detail=exception.message)
        return wrapper
    return decorator