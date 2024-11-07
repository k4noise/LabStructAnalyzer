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
class TableElement(IParserElement[List[List[CellElement]]]):
    """Элемент таблицы"""

    data: List[List[CellElement]]

    def __post_init__(self) -> None:
        super().__init__(ParserElementType.TABLE, self.data)

    def to_dict(self) -> dict:
        return {
            "type": self.element_type.value,
            **self.collect_common_fields(),
            "data": [y.to_dict() for sublist in self.data for y in sublist],
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
