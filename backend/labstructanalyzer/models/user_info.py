from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class UserInfoDto(BaseModel):
    """
    Базовые данные о пользователе из LMS
    """
    full_name: str

    model_config = ConfigDict(serialize_by_alias=True, populate_by_name=True, alias_generator=to_camel)
