from pylti1p3.message_launch import MessageLaunch

from labstructanalyzer.services.lti.course import CourseService
from labstructanalyzer.services.lti.user import User


class JWT:
    """
    Сервис подготовки данных для токенов JWT
    """

    def create_user_claims_at_jwt_object(self, raw_jwt: dict) -> dict:
        """
        Создает объект пользовательских данных на основе данных из другого jwt
        """
        return self._create_user_claims(raw_jwt.get("roles"), raw_jwt.get("launch_id"), raw_jwt.get("course_id"))

    def create_user_claims_at_message_launch(self, message_launch: MessageLaunch) -> dict:
        """
        Создает объект пользовательских данных на основе данных из данных запуска LTI
        """
        roles = User(message_launch).get_roles()
        launch_id = message_launch.get_launch_id()
        course_id = CourseService(message_launch).get_id()
        return self._create_user_claims(roles, launch_id, course_id)

    def _create_user_claims(self, roles: list[str], launch_id: str, course_id: str) -> dict:
        """
        Создает универсальный объект пользовательских данных
        """
        return {
            "roles": roles,
            "launch_id": launch_id,
            "course_id": course_id
        }
