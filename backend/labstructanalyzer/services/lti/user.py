from typing import List

from pylti1p3.message_launch import MessageLaunch


class User:
    """
    Сервис обработки данных пользователя из данных запуска
    """

    def __init__(self, message_launch: MessageLaunch):
        self.message_launch = message_launch
        self.launch_data = message_launch.get_launch_data()

    def get_id(self) -> str:
        """
        Возвращает id пользователя
        """
        return self.launch_data.get("sub")

    def get_avatar_url(self) -> str:
        """
        Возвращает url аватара пользователя (только для LMS Moodle)
        """
        return f"{self.message_launch.get_iss()}/user/pix.php/{self.get_id()}/f1.jpg"

    def get_full_name(self):
        """
        Возвращает имя пользователя полностью - ФИО
        """
        return self.launch_data.get("name")

    def get_name(self):
        """
        Возвращает только имя пользователя
        """
        return self.launch_data.get("given_name")

    def get_surname(self):
        """
        Возвращает только фамилию пользователя
        """
        return self.launch_data.get("family_name")

    def get_roles(self) -> List[str]:
        """
        Получить роли пользователей
        """
        roles = []
        if self.message_launch.check_teacher_access():
            roles.append("teacher")
        elif self.message_launch.check_teaching_assistant_access():
            roles.append("assistant")
        elif self.message_launch.check_student_access():
            roles.append("student")
        return roles
