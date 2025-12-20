from contextlib import suppress
from typing import Optional

from pydantic import ValidationError
from pylti1p3.message_launch import MessageLaunch

from labstructanalyzer.core.logger import GlobalLogger
from labstructanalyzer.exceptions.lis_service_no_access import NrpsNotSupportedException
from labstructanalyzer.schemas.user import NrpsUser
from labstructanalyzer.services.lti.course import CourseService


class NrpsService:
    """
    Методы для получения данных пользователя из службы ролей и имен LTI NRPS
    """

    def __init__(self, message_launch: MessageLaunch):
        if not message_launch.has_nrps():
            raise NrpsNotSupportedException()
        self.message_launch = message_launch
        self.logger = GlobalLogger().get_logger(__name__)
        self._members_map: Optional[dict[str, NrpsUser]] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_user_by_id(self, user_id: str) -> Optional[NrpsUser]:
        """Получить данные из NRPS по идентификатору пользователя"""
        self._ensure_members_loaded()
        return self._members_map.get(user_id)

    def _ensure_members_loaded(self) -> None:
        """Загружает данные, если они еще не были загружены"""
        if self._members_map is None:
            members = self.message_launch.get_nrps().get_members()
            self.logger.warning(f"Получен доступ к данным NRPS в курсе {CourseService(self.message_launch).name}")

            self._members_map = {}
            for user_data in members:
                with suppress(ValidationError):
                    self._members_map[user_data.get("user_id")] = NrpsUser.model_validate(user_data)
