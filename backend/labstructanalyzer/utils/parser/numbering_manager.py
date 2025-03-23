from collections import namedtuple
import re
from dataclasses import asdict, dataclass
from typing import Optional

NumberingProps = namedtuple("NumberingProps", ["id", "ilvl"])


@dataclass
class NumberingItem:
    """Данные нумерации

    Args:
      format: Формат маркера
      startValue: Начальное значение пункта нумерации
      text: Текстовое представление пункта нумерации, для подстановки значения в тексте используются %d, где d - уровень нумерации + 1
    """

    format: str
    startValue: int
    text: str


class NumberingManager:
    """Система управления нумерациями.
    Производит расчеты и преобразования для корректного вычисления текстовых маркеров пунктов списков нумерации различных типов.
    Поддерживается как одноуровневая, так и многоуровневая нумерация.
    Для многоуровневой нумерации справедливо следующее: при увеличении значения пункта значения уровня N у всех пунктов уровня >N обнуляется значение пункта

    Attributes:
      ROMAN_SYMBOLS: Вспомогательный массив кортежей для преобразования арабских цифр в греческие
      numberings: Словарь, хранящий данные нумерации, использует схему [id нумерации][уровень нумерации] = { данные }
    """

    ROMAN_SYMBOLS = [
        ("m", 1000),
        ("cm", 900),
        ("d", 500),
        ("cd", 400),
        ("c", 100),
        ("xc", 90),
        ("l", 50),
        ("xl", 40),
        ("x", 10),
        ("ix", 9),
        ("v", 5),
        ("iv", 4),
        ("i", 1),
    ]

    def __init__(self) -> None:
        """Инициализирует объект класса Numbering и создает словарь для хранения данных нумераций"""
        self.numberings = {}

    def add_numbering_data(
            self, id: str, ilvl: int, numbering_data: NumberingItem
    ) -> None:
        """Сохраняет данные элемента нумерации, если ранее не сохранялись

        Args:
          id: Идентификатор нумерации
          ilvl: Уровень нумерации
          numbering_data: Данные нумерации
        """
        if not numbering_data:
            return

        if not self.numberings.get(id):
            self.numberings[id] = {}
        elif self.has_numbering(id, ilvl):
            return

        self.numberings[id][ilvl] = {
            "value": numbering_data.startValue - 1,
            **asdict(numbering_data),
        }

    def get_next_point_text_value(self, id: str, ilvl: int) -> Optional[str]:
        """Возвращает текстовое представление следующего маркера пункта при корректных данных идиентификатора и уровня, подставляя значения.
        Важно! Если список многоуровневый, выполняется обнуление значений всех уровней, больше текущего

        Args:
          id: Идентификатор нумерации
          ilvl: Уровень нумерации

        Returns:
          Текстовое представление маркера следующего пункта
        """
        if not self.has_numbering(id, ilvl):
            return None
        self.numberings[id][ilvl]["value"] += 1
        self._reset_deeper_levels_values(id, ilvl)
        return self._insert_values_into_point_text(
            self.numberings[id][ilvl]["text"], id, ilvl
        )

    def has_numbering(self, id: str, ilvl: int) -> bool:
        """Указывает, были ли сохранены данные нумерации для данного идентификатора нумерации и уровня нумерации

        Args:
          id: Идентификатор нумерации
          ilvl: Уровень нумерации

        Returns:
          Булево значения наличия данных нумерации
        """
        return bool(self.numberings.get(id, {}).get(ilvl))

    def _reset_deeper_levels_values(self, id: str, ilvl: int) -> None:
        """Выполняет сброс значений пунктов уровней для уровней больше представленного
        Если список многоуровневый, выполняется обнуление значений всех уровней, больше текущего

        Args:
          id: Идентификатор нумерации
          ilvl: Уровень нумерации
        """
        for numbering_level in self.numberings[id].keys():
            if numbering_level <= ilvl:
                continue
            self.numberings[id][numbering_level]["value"] = (
                    self.numberings[id][numbering_level]["startValue"] - 1
            )

    def _insert_values_into_point_text(self, text: str, id: int, ilvl: int) -> str:
        """Выполняет подстановку значения пункта в текст с учетом типа значения

        Args:
          text: Текстовое представление значения пункта с метками %ilvl+1 для подстановки значений(я)
          id: Идентификатор нумерации

        Returns:
          Текстовое представление маркера пункта с подставленным значением
        """
        if "%" in text:
            for match in re.finditer(r"%(\d+)", text):
                ilvl = int(match.group(1)) - 1
                point_value = self._convert_point_value_text(self.numberings[id][ilvl]) if ilvl in self.numberings[
                    id] else ""
                text = text.replace(match.group(0), str(point_value))
        else:
            return self._convert_point_value_text(self.numberings[id][ilvl])
        return text

    def _convert_point_value_text(self, numbering_data: NumberingItem) -> str:
        """Преобразует значение в формат, указанный в данных нумерации

        Args:
          numbering_data: Данные нумерации

        Returns:
          Преобразованное в указанный формат значение пункта
        """
        match numbering_data["format"]:
            case "bullet":
                return self._get_printable_bullet(numbering_data["text"])
            case "decimal":
                return numbering_data["value"]
            case "lowerLetter":
                return self._convert_to_lower_letter(numbering_data["value"])
            case "upperLetter":
                return self._convert_to_lower_letter(numbering_data["value"]).upper()
            case "lowerRoman":
                return self._convert_to_lower_roman(numbering_data["value"])
            case "upperRoman":
                return self._convert_to_lower_roman(numbering_data["value"]).upper()

    def _get_printable_bullet(self, bullet: str) -> str:
        """Возвращает отображаемую версию маркера.
        Обрабатывает случай, когда текстовый процессор использует неотображаемый символ и для его отображения использует специальные шрифты, и заменяет символ на отображаемый

        Args:
          bullet: Текст маркера

        Returns:
          Текст маркера, если он является отображаемым, или символ маркера по умолчанию
        """
        DEFAULT_PRINTABLE_BULLET = "•"
        return bullet if bullet.isprintable() else DEFAULT_PRINTABLE_BULLET

    def _convert_to_lower_letter(self, point_value: int) -> chr:
        """Выполняет конвертацию значения пункта в строчную латинскую букву

        Args:
          point_value: Значение пункта

        Returns:
          Символ, соответствующий значению пункта
        """
        ASCII_CODE_LOWERCASE_A = 97
        return chr(ASCII_CODE_LOWERCASE_A - 1 + point_value)

    def _convert_to_lower_roman(self, point_value: int) -> str:
        """Выполняет конвертацию значения пункта в строчные греческие цифры

        Args:
          point_value: Значение пункта

        Returns:
          Греческие цифры, соответствующие значению пункта
        """
        roman_numeral = ''
        for symbol, value in self.ROMAN_SYMBOLS:
            while point_value >= value:
                roman_numeral += symbol
                point_value -= value
        return roman_numeral
