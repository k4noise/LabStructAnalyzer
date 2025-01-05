from fastapi import HTTPException
from starlette import status


async def invalid_jwt_state(request, exc):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")


async def invalid_lti_state(request, exc):
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Ошибка внешнего инструмента")


async def no_existing_template(request, exc):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


async def no_ags_service_access(request, exc):
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.message)