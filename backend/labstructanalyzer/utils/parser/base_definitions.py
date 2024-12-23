from abc import ABC, abstractmethod
from enum import Enum
from typing import Generic, Optional, TypeVar

DataType = TypeVar("DataType")


class ParserElementType(Enum):
    """Возможные элементы парсера"""

    IMAGE = "image"
    TEXT = "text"
    TABLE = "table"
    CELL = "cell"


class IParserElement(ABC, Generic[DataType]):
    """Абстрактный базовый класс элементов парсера"""

    nesting_level: Optional[int] = None
    numbering_level: Optional[int] = None
    numbering_bullet_text: Optional[str] = None
    is_cell_element: bool = False

    _property_to_json_map = [
        ("nestingLevel", "nesting_level"),
        ("numberingBulletText", "numbering_bullet_text"),
    ]

    def __init__(self, element_type: ParserElementType, data: DataType) -> None:
        self.element_type = element_type
        self.data = data

    @abstractmethod
    def to_dict(self) -> dict:
        """Абстрактный метод для преобразования данных элемента парсера в словарь"""
        pass

    def collect_common_fields(self) -> dict:
        """Сбор общих свойств любого элемента парсера"""
        return {
            "type": self.element_type.value,
            **{
                key: getattr(self, attr)
                for key, attr in self._property_to_json_map
                if getattr(self, attr) is not None
            },
        }

