from dataclasses import dataclass, field
from typing import List, Optional

from labstructanalyzer.utils.parser.base_definitions import IParserElement, ParserElementType


@dataclass
class ImageElement(IParserElement[str]):
    """Элемент изображения"""

    data: str

    def __post_init__(self) -> None:
        super().__init__(ParserElementType.IMAGE, self.data)

    def to_dict(self) -> dict:
        return {
            "type": self.element_type.value,
            "data": self.data,
            **self.collect_common_fields(),
        }


@dataclass
class CellElement(IParserElement[List[IParserElement]]):
    """Элемент ячейки таблицы"""

    data: List[IParserElement] = field(default_factory=list)
    merged: Optional[bool] = field(default=None)
    rows: Optional[int] = field(default=1)
    cols: Optional[int] = field(default=1)

    def __post_init__(self) -> None:
        if self.rows > 1 or self.cols > 1:
            self.merged = True
        super().__init__(ParserElementType.CELL, self.data)

    def to_dict(self) -> dict:
        data = {
            "type": self.element_type.value,
            "data": [x.to_dict() for x in self.data],
            **self.collect_common_fields(),
        }
        if self.merged:
            data.update(
                {
                    "merged": True,
                    **{
                        k: v
                        for k, v in [("rows", self.rows), ("cols", self.cols)]
                        if v > 1
                    },
                }
            )
        return data


@dataclass
class RowElement(IParserElement[List[CellElement]]):
    """Элемент строки таблицы"""
    data: List[CellElement]

    def __post_init__(self) -> None:
        super().__init__(ParserElementType.ROW, self.data)

    def to_dict(self) -> dict:
        return {
            "type": self.element_type.value,
            "data": [cell.to_dict() for cell in self.data],
            **self.collect_common_fields(),
        }


@dataclass
class TableElement(IParserElement[List[RowElement]]):
    """Элемент таблицы"""

    data: List[RowElement]

    def __post_init__(self) -> None:
        super().__init__(ParserElementType.TABLE, self.data)

    def to_dict(self) -> dict:
        return {
            "type": self.element_type.value,
            **self.collect_common_fields(),
            "data": [row.to_dict() for row in self.data],
        }


@dataclass
class TextElement(IParserElement[str]):
    """Элемент текста"""

    data: str
    style_id: Optional[str] = None
    header_level: Optional[int] = field(default=None)

    def __post_init__(self) -> None:
        super().__init__(ParserElementType.TEXT, self.data)

    def to_dict(self) -> dict:
        data = {
            "type": self.element_type.value,
            "data": self.data,
            **self.collect_common_fields(),
        }
        if self.header_level:
            data.update({"headerLevel": self.header_level})
        return data


@dataclass
class QuestionElement(IParserElement[list[IParserElement]]):
    """Элемент вопроса"""

    data: list[IParserElement]

    def __post_init__(self) -> None:
        super().__init__(ParserElementType.QUESTION, self.data)

    def to_dict(self) -> dict:
        return {
            "type": self.element_type.value,
            "data": self.data,
            **self.collect_common_fields(),
        }

@dataclass
class AnswerElement(IParserElement[str]):
    """Элемент ответа"""

    data: str
    weight: int = field(default=1)
    simple: bool = field(default=True)

    def __post_init__(self) -> None:
        super().__init__(ParserElementType.ANSWER, self.data)

    def to_dict(self) -> dict:
        properties = {
            "type": self.element_type.value,
            "data": self.data,
            "weight": self.weight,
            "simple": self.simple,
            **self.collect_common_fields(),
        }
        return properties