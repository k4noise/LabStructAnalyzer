from labstructanalyzer.domain.report_status import ReportStatus


class AccessDeniedException(Exception):
    """Исключение, возникающее при отсутствии доступа к ресурсу"""

    def __init__(self, reason: str):
        super().__init__(f"Доступ запрещен: {reason}")


class RoleAccessDeniedException(AccessDeniedException):
    """Исключение, возникающее при отсутствии прав доступа пользователя к ресурсу"""

    def __init__(self):
        super().__init__("недопустимые права")


class NotOwnerAccessDeniedException(AccessDeniedException):
    """Исключение, возникающее при попытке доступа не создателем ресурса"""

    def __init__(self):
        super().__init__("пользователь не является автором")


class InvalidCourseAccessDeniedException(AccessDeniedException):
    """Исключение, возникающее при попытке доступа к сущности другого курса"""

    def __init__(self):
        super().__init__("шаблон или отчет другого курса")


class ReportStateAccessDeniedException(AccessDeniedException):
    """Исключение, возникающее при попытке доступа преподавателем / ассистентом к недоступному для просмотра отчету"""

    def __init__(self, status: ReportStatus):
        super().__init__(f"отчет недоступен для инструктора - статус {str(status)}")
