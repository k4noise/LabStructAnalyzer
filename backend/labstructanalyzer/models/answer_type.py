import enum


class AnswerType(enum.Enum):
    simple = "Фиксированный"
    param = "Параметризованный"
    arg = "Описательный"
