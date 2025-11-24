import re
from functools import lru_cache
from typing import List, Tuple, Union


class RangeSpec:
    """
    Представляет спецификацию диапазона из строки вида:
        "1-5 | 7 | A | 3.5 | -1.5 - 2.5"

    Поддерживает:
    - целые числа (`int`)
    - числа с плавающей точкой (`float`)
    - диапазоны (`start - end`)
    - строки (любые неприводимые к числу)

    Используется для валидации и построения регулярки с соответствием
    """

    _RE_RANGE_FLOAT = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\s*$")
    _RE_FLOAT = re.compile(r"^[+-]?\d+\.\d+$")
    _RE_INT = re.compile(r"^[+-]?\d+$")
    _RE_NUMERIC = re.compile(r"^-?\d+(?:\.\d+)?$")

    def __init__(self, raw: str):
        """
        Парсит спецификацию строки (без скобок [ ]) и заполняет список частей выражения.
        Частями выражения считается содержимое, разделителем которого является `|`

        Args:
            raw: строка диапазона, например "1 - 5 | abc | 8.9"
        """
        self.raw = raw.strip()
        self.parts: List[Union[int, float, str, Tuple[Union[int, float], Union[int, float]]]] = []

        for token in (tok.strip() for tok in self.raw.split("|") if tok.strip()):
            if match := self._RE_RANGE_FLOAT.fullmatch(token):
                start_raw, end_raw = match.group(1), match.group(2)
                if '.' in start_raw or '.' in end_raw:
                    start, end = sorted((float(start_raw), float(end_raw)))
                else:
                    start, end = sorted((int(start_raw), int(end_raw)))
                self.parts.append((start, end))
            elif self._RE_INT.fullmatch(token):
                self.parts.append(int(token))
            elif self._RE_FLOAT.fullmatch(token):
                self.parts.append(float(token))
            else:
                self.parts.append(token)

    @classmethod
    @lru_cache(maxsize=256)
    def from_raw(cls, raw: str) -> "RangeSpec":
        """
        Кэшированная фабрика для парсинга спецификаций

        Args:
            raw: спецификация диапазона без квадратных скобок

        Returns:
            RangeSpec: экземпляр для диапазона
        """
        return cls(raw)

    @property
    def is_numeric(self) -> bool:
        """
        True, если все части — числа или диапазоны чисел
        """
        return all(not isinstance(part, str) for part in self.parts)

    @property
    def is_float(self) -> bool:
        """
        True, если в частях есть хотя бы один float (или float-диапазон)
        """
        for part in self.parts:
            if isinstance(part, float):
                return True
            if isinstance(part, tuple) and any(isinstance(subpart, float) for subpart in part):
                return True
        return False

    @property
    def is_mixed(self) -> bool:
        """
        True, если части одновременно содержат строки и числа
        """
        has_str = any(isinstance(part, str) for part in self.parts)
        has_num = any(isinstance(part, (int, float, tuple)) for part in self.parts)
        return has_str and has_num

    @property
    def values(self) -> List[Union[int, float, str]]:
        """
        Возвращает развёрнутый список значений:
        - Если диапазон: все значения (для int) или просто (start, end) для float
        - Если константа — как есть
        """
        result: List[Union[int, float, str]] = []

        for part in self.parts:
            if isinstance(part, tuple):
                start, end = part
                if isinstance(start, int) and isinstance(end, int) and not self.is_float:
                    result.extend(range(start, end + 1))
                else:
                    result.extend([start, end])
            else:
                result.append(part)

        return result

    def regex_fragment(self) -> str:
        """
        Возвращает шаблон regex для встраивания в выражение:
        - Числа: (-?\\d+) или (-?\\d+(?:\\.\\d+)?)
        - Строки: (\\S+)
        """
        if self.is_numeric:
            return r"(-?\d+(?:\.\d+)?)" if self.is_float else r"(-?\d+)"
        return r"(\S+)"

    def match(self, text: str) -> bool:
        """
        Проверяет, совпадает ли text с любой частью спецификации.

        Args:
            text: значение пользователя

        Returns:
            bool: True, если text удовлетворяет spec
        """
        stripped = text.strip()

        is_number_like = self._RE_NUMERIC.fullmatch(stripped)
        if is_number_like:
            try:
                value = float(stripped) if '.' in stripped else int(stripped)
                for part in self.parts:
                    if isinstance(part, tuple):
                        start, end = part
                        if start <= value <= end:
                            return True
                    elif isinstance(part, (int, float)):
                        if value == part:
                            return True
            except ValueError:
                pass

        lowered = stripped.lower()
        return any(str(part).lower() == lowered for part in self.parts)

    def __repr__(self) -> str:
        return (
            f"RangeSpec(raw={self.raw!r}, "
            f"values={self.values!r}, "
            f"is_numeric={self.is_numeric}, "
            f"is_float={self.is_float}, "
            f"is_mixed={self.is_mixed})"
        )
