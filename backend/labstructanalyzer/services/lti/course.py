from pylti1p3.message_launch import MessageLaunch


class CourseService:
    """
    Сервис обработки данных курса пользователя из данных запуска или через сервис NRPS LTI 1.3
    """

    def __init__(self, message_launch: MessageLaunch):
        self.message_launch = message_launch
        self.course_data = message_launch \
            .get_launch_data() \
            .get("https://purl.imsglobal.org/spec/lti/claim/context")

    def get_name(self) -> str:
        """
        Получить имя курса
        """
        return self.course_data.get("title")

    def get_id(self) -> str:
        """
        Получить id курса
        """
        if "id" in self.course_data:
            return self.course_data.get("id")
