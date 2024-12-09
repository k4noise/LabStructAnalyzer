from typing import List

from pylti1p3.message_launch import MessageLaunch


class LTIRoles:
    """
    Сервис обработки ролей пользователя
    """
    def __init__(self, data: MessageLaunch):
        self.data = data

    def get_role(self) -> List[str]:
        """
        Получить роли пользователей
        """
        roles = []
        if self.data.check_staff_access():
            roles.append("teacher")
        elif self.data.check_teaching_assistant_access():
            roles.append("assistant")
        elif self.data.check_student_access():
            roles.append("student")
        return roles