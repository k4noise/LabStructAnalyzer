import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CreateTemplate(BaseModel):
    user_id: str
    course_id: str
    name: str

    model_config = ConfigDict(frozen=True)


class UpdateTemplate(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    max_score: Optional[int] = None
    is_draft: Optional[bool] = None
    updated_at: datetime = datetime.now()

    model_config = ConfigDict(frozen=True)
