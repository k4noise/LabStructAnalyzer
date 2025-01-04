from typing import List

from pydantic import BaseModel, HttpUrl


class UserInfo(BaseModel):
    """
    Базовые данные о пользователе из LMS
    """
    fullName: str
    name: str
    surname: str
    role: List[str]
    avatarUrl: HttpUrl
