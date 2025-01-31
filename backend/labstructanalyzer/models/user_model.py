import enum
from typing import List

from pydantic import BaseModel


class UserRole(enum.Enum):
    """Роли пользователя"""
    STUDENT = 'student',
    ASSISTANT = 'assistant',
    TEACHER = 'teacher'


class User(BaseModel):
    """Модель данных пользователя, получаемая из JWT-токена"""
    sub: str
    roles: List[UserRole]
    launch_id: str
    course_id: str
