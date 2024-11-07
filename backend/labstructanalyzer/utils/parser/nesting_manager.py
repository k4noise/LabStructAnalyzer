from typing import Optional
from labstructanalyzer.utils.parser.base_definitions import IParserElement
from labstructanalyzer.utils.parser.common_elements import TextElement


class NestingManager:
    """Система управления уровнями вложенности.
    Позволяет корректно рассчитать уровень вложенности для любого вида элемента, корректно расчитывает для элементов ячейки таблицы. Рассчет выполняется максимально независимым от предыдущего вычисления и однозначным

    Attributes:
      last_header_level: Уровень последнего найденного заголовка
    """

    last_header_level = 0

    def get_level(self, element: IParserElement) -> Optional[int]:
        """Возвращает уровень вложенности элемента.
        Вычисляется на основании данных вложенности списка (при наличии) с корректировкой на вложенность нумерации относительно уровня последнего обработанного заголовка.
        Для элементов внутри ячейки заголовки игнорируются.

        Args:
          element: Извлеченный парсерами IContentParser элемент

        Returns:
            None, если содержимое ячейки не является элементом списка или уровень вложенности
        """
        last_header_level = 0 if element.is_cell_element else self.last_header_level
        if (
            isinstance(element, TextElement)
            and element.header_level
            and not element.is_cell_element
        ):
            self.last_header_level = element.header_level
            return element.header_level
        elif element.numbering_level is not None:
            shifted_numbering_level = element.numbering_level + 1
            if shifted_numbering_level > last_header_level:
                return shifted_numbering_level
            elif shifted_numbering_level == last_header_level:
                return last_header_level + 1
        return None if element.is_cell_element else last_header_level + 1
