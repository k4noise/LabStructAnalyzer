from enum import Enum
from typing import Callable

from labstructanalyzer.utils.parser.base_definitions import IParserElement


class CheckStatus(Enum):
    """Возможные статусы проверки элемента на соответствие условию"""
    VALID = "valid"
    UNVALID = "unvalid"
    SKIP = "skip"


class FixedChecker:
    """Класс для проверки конкретного значения атрибута элемента

       Атрибуты:
           key: Имя атрибута элемента, который нужно проверить
           expected_value: Ожидаемое значение атрибута
           callback: Функция обратного вызова для сравнения значений
       """

    def __init__(self, key: str, expected_value: str, callback: Callable[[str, str], bool]):
        self.key = key
        self.expected_value = expected_value
        self.callback = callback

    def check(self, element: IParserElement) -> CheckStatus:
        """Проверяет элемент на соответствие ожидаемому значению

            Args:
                element: Элемент для проверки.

            Returns:
                Статус проверки CheckStatus
               """
        if hasattr(element, self.key):
            return (
                CheckStatus.VALID
                if self.callback(str(getattr(element, self.key)), str(self.expected_value))
                else CheckStatus.UNVALID
            )
        else:
            return CheckStatus.SKIP


class CommonChecker:
    """
    Класс для создания FixedChecker с конкретным ожидаемым значением

    Атрибуты:
        key: Имя атрибута элемента, который нужно проверять
        callback: Функция обратного вызова для проверки значений
    """

    def __init__(self, key: str, callback: Callable[[str, str], bool]):
        self.key = key
        self.callback = callback

    def register(self, expected_value: str) -> FixedChecker:
        """Создает и returns FixedChecker с указанным ожидаемым значением

        Args:
            expected_value: Ожидаемое значение атрибута

        Returns:
            Экземпляр FixedChecker для проверки конкретного значения
          """
        return FixedChecker(self.key, expected_value, self.callback)


class DirectChecker:
    """Класс для прямой проверки элемента без указания конкретного атрибута.
    Используется только в том случае, если другие чекеры использовать невозможно

    Атрибуты:
        callback: Функция обратного вызова для проверки элемента
    """

    def __init__(self, callback: Callable[[IParserElement, any], bool]):
        self.callback = callback
        self.expected = None

    def register(self, expected_value: str) -> 'DirectChecker':
        """
        Этот метод не используется для DirectChecker, но реализован для совместимости с интерфейсом.

        Args:
            expected_value: Игнорируется для DirectChecker

        Returns:
            Сам объект DirectChecker
        """
        self.expected = expected_value
        return self

    def check(self, element: IParserElement) -> CheckStatus:
        """
        Проверяет элемент, используя callback функцию

        Args:
            element: Элемент для проверки

        Returns:
            Статус проверки CheckStatus
        """
        return (
            CheckStatus.VALID
            if self.callback(element, self.expected)
            else CheckStatus.UNVALID
        )

class CheckerRegistry:
    """Класс для управления регистрацией и созданием чекеров

    Атрибуты:
        checkers (dict): Словарь зарегистрированных чекеров
    """

    def __init__(self):
        self.checkers = {}

    def get_properties(self):
        """
        Returns список зарегистрированных ключей

        Returns:
            Ключи зарегистрированных чекеров
        """
        return self.checkers.keys()

    def create_common(self, prop: str, key: str, check_callback: Callable[[str, str], bool]):
        """
        Создает и регистрирует новый CommonChecker

        Args:
            prop: Свойство, характеризующее проверку
            key: Имя атрибута, который нужно проверять
            check_callback: Функция обратного вызова для проверки значений

        Throws:
            ValueError: Если ключ уже зарегистрирован.
        """
        if self.checkers.get(prop):
            raise ValueError(f"Key exists: {prop}")
        self.checkers[prop] = CommonChecker(key, check_callback)

    def create_fixed(self, key: str, expected_value: str) -> FixedChecker | DirectChecker:
        """Создает FixedChecker для указанного ключа и ожидаемого значения.
        Создание чекера невозможно, если не создан чекер типа common/direct для указанного ключа

         Args:
             key: Имя атрибута, который нужно проверять
             expected_value: Ожидаемое значение атрибута

         Returns:
             Экземпляр FixedChecker для проверки значения

         Throws:
             ValueError: Если ключ не зарегистрирован
         """
        checker = self.checkers.get(key)
        if checker:
            return checker.register(expected_value)
        else:
            raise ValueError(f"Unknown key: {key}")

    def create_direct(self, prop: str, callback: Callable[[IParserElement, any], bool]):
        if self.checkers.get(prop):
            raise ValueError(f"Key exists: {prop}")
        self.checkers[prop] = DirectChecker(callback)