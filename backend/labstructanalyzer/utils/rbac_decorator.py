from typing import List, Callable

from fastapi import HTTPException, Depends
from fastapi_another_jwt_auth import AuthJWT
from fastapi_another_jwt_auth.exceptions import AuthJWTException


def roles_required(roles: List[str]) -> Callable:
    def decorator(func: Callable) -> Callable:
        async def wrapper(authorize: AuthJWT = Depends()) -> Callable:
            try:
                authorize.jwt_required()
                user_roles = authorize.get_raw_jwt().get("role")
                if not any(item in roles for item in user_roles):
                    raise HTTPException(status_code=403, detail="Доступ запрещен")
                return await func(authorize)
            except AuthJWTException as exception:
                raise HTTPException(status_code=exception.status_code, detail=exception.message)
        return wrapper
    return decorator