from typing import List

from labstructanalyzer.utils.parser.base_definitions import IParserElement
from labstructanalyzer.utils.parser.structure.checkers import CheckerRegistry, CheckStatus


class BaseStructureComponent:
    """Класс для базовых компонентов структуры

    Атрибуты:
        structure_props: Свойства структуры
        validators: Список валидаторов для проверки компонентов
    """

    def __init__(self, checker_registry: CheckerRegistry, json_part: dict):
        """Инициализирует BaseStructureComponent с заданным реестром чекеров и частью JSON

        Аргументы:
            checker_registry: Реестр чекеров для проверки компонентов
            json_part: Часть JSON для инициализации компонента
        """
        self.structure_type = json_part.get("type")
        self.content_type = json_part.get("contentType")
        self.structure_props = json_part
        self.validators = {}

        for check_property in checker_registry.get_properties():
            if json_part.get(check_property):
                self.validators[check_property] = checker_registry.create_fixed(check_property,
                                                                                json_part[check_property])

    def validate(self, element: IParserElement):
        """Проверяет элемент на соответствие установленным валидаторам

        Args:
            element: Элемент для проверки

        Returns:
            True, если элемент соответствует всем валидаторам, иначе False
        """
        if self.content_type != element.element_type.value:
            return False

        for checker in self.validators.values():
            if checker.check(element) is CheckStatus.UNVALID:
                return False

        return True

    def apply_structure(self, element: IParserElement) -> dict:
        """Применяет структуру к элементу и возвращает обновленный словарь

        Args:
            element: Элемент для применения структуры

        Returns:
            Обновленный словарь элемента
        """
        element_in_dict = element.to_dict()
        element_in_dict.update(self.structure_props)
        for key in self.validators.keys():
            element_in_dict.pop(key)

        return element_in_dict


class CompositeStructureComponent:
    """Класс для составных компонентов структуры

    Атрибуты:
        structure_props: Свойства структуры
        components: Список базовых компонентов
        chunk_count: Количество элементов в чанке
    """

    def __init__(self, checker_registry: CheckerRegistry, json_part: dict):
        """Инициализирует CompositeStructureComponent с заданным реестром чекеров и частью JSON.

        Args:
            checker_registry: Реестр чекеров для проверки компонентов
            json_part: Часть JSON для инициализации компонента
        """
        self.structure_props = json_part
        self.data = [
            BaseStructureComponent(checker_registry, component_json) for component_json in json_part.get("data")
        ]
        self.chunk_count = len(self.data)

    def validate(self, elements: List[IParserElement]) -> bool:
        """Проверяет список элементов на соответствие установленным валидаторам

        Args:
            elements: Список элементов для проверки

        Returns:
            True, если все элементы соответствуют валидаторам, иначе False
        """
        if len(self.data) > len(elements):
            return False

        for component, element in zip(self.data, elements):
            if not component.validate(element):
                return False
        return True

    def get_structure_template(self):
        """Возвращает свойства составного компонента"""
        return self.structure_props.copy()
