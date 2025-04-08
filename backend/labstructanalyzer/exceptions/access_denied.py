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
