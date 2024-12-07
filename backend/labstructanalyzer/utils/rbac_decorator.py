from typing import List, Callable

from fastapi import HTTPException, Depends
from fastapi_jwt_auth import AuthJWT


def roles_required(roles: List[str]) -> Callable:
    def decorator(func: Callable) -> Callable:
        async def wrapper(authorize: AuthJWT = Depends(), *args, **kwargs) -> Callable:
            authorize.jwt_required()
            user_claims = authorize.get_raw_jwt()
            if user_claims.get("role") not in roles:
                raise HTTPException(status_code=403, detail="Доступ запрещен")
            return await func(authorize, *args, **kwargs)
        return wrapper
    return decorator