from pydantic import BaseModel, HttpUrl


class UserCourseInfo(BaseModel):
    """
    Базовые данные о пользователе из LMS
    """
    fullName: str
    avatarUrl: HttpUrl
    courseName: str