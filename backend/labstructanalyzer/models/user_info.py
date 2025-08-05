from pydantic import BaseModel, ConfigDict, Field


class UserInfoDto(BaseModel):
    """
    Базовые данные о пользователе из LMS
    """
    full_name: str = Field(alias="fullName")

    model_config = ConfigDict(serialize_by_alias=True)
