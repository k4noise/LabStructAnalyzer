import enum
from typing import List

from pydantic import BaseModel, field_validator


class UserRole(enum.Enum):
    """Роли пользователя"""
    STUDENT = 'student'
    ASSISTANT = 'assistant'
    TEACHER = 'teacher'


class User(BaseModel):
    """Модель данных пользователя, получаемая из JWT-токена"""
    sub: str
    roles: List[UserRole]
    launch_id: str
    course_id: str

    @field_validator('roles', mode='before')
    def convert_roles_to_enum(cls, raw_roles: List[str | UserRole]) -> List[UserRole]:
        """Конвертирует строку с ролью в соответствующее значение UserRole"""
        result = []
        for role in raw_roles:
            if isinstance(role, str):
                result.append(UserRole(role))
            else:
                result.append(role)
        return result
