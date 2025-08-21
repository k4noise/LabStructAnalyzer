class InvalidActionException(Exception):
    """Исключение, возникающее при выполнении действия, приводящего к конфликту"""

    def __init__(self, reason: str):
        super().__init__(f"Конфликт действия: {reason}")


class InvalidTransitionException(InvalidActionException):
    """Исключение, возникающее при попытке перехода в запрещенное состояние"""

    def __init__(self):
        super().__init__("недопустимый переход состояния отчета")
