from pylti1p3.message_launch import MessageLaunch

from labstructanalyzer.exceptions.lis_service_no_access import NrpsNotSupportedException
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.services.lti.course import CourseService

USERS_TTL = 24 * 60 * 60  # сутки


class NrpsService:
    """
    Методы для получения данных пользователя из службы ролей и имен LTI NRPS
    """

    def __init__(self, message_launch: MessageLaunch):
        if not message_launch.has_nrps():
            raise NrpsNotSupportedException()

        self.message_launch = message_launch
        self.course_id = CourseService(self.message_launch).get_id()

    def get_user_name(self, user_id):
        """
        Получить имя пользователя по идентификатору.
        Если данные курса отсутствуют в кеше, то они сохраняются в кеш.
        """
        course_users = cache.get(self.course_id)
        if course_users is not None:
            return course_users.get(str(user_id))

        self._cache_users()
        return self.get_user_name(user_id)

    def _cache_users(self):
        """
        Получить данные из LMS о всех пользователях и сохранить в кеше для быстрого доступа
        """
        users = self.message_launch \
            .get_nrps() \
            .get_members()

        users_dict = {user['user_id']: user['name'] for user in users}
        cache.set(self.course_id, users_dict, USERS_TTL)
