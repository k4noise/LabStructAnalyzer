from __future__ import annotations

import re
from typing import Dict, List, Optional

from labstructanalyzer.models.dto.answer import FullAnswerData, GradeResult


class ParametrizedAnswerGrader:
    """
    Проверяет ответы с параметрами {param} и диапазонами/наборами [1-5], [2|3].
    Если имеются параметры, предварительно оцененные как неверные, то и ответ тоже будет оценен как неверный.
    Ответ верен, если все проверки пройдены и все тезисы присутствуют
    """

    _RE_PARAM = re.compile(r"\{([^}]+)}")
    _RE_RANGE = re.compile(r"\[(.*?)\]")
    _RE_SPACE = re.compile(r"\s+")
    _RE_DIGITS = re.compile(r"\d+")

    def __init__(self, parameters: Dict[str, FullAnswerData]) -> None:
        self._parameters = parameters

    def grade(self, given: str, reference: str) -> GradeResult:
        """Оценивает ответ на соответствие эталонному ответу

        Args:
            given: Ответ пользователя
            reference: Эталонный ответ

        Returns:
            Результат оценки
        """
        given_norm = self._normalize(given)
        reference_theses = [l.strip() for l in reference.splitlines() if l.strip()]

        if not reference_theses:
            return GradeResult(score=1, comment="Эталон пуст")

        errors: List[str] = []
        for thesis in reference_theses:
            line, sub_errors = self._substitute_params(thesis)
            errors.extend(sub_errors)

            error = self._validate_line(line, given_norm)
            if error:
                errors.append(error)

        return GradeResult(score=0, comment="\n".join(errors)) if errors else GradeResult(score=1)

    def _substitute_params(self, line: str) -> tuple[str, list[str]]:
        """Выполняет подстановку параметров в эталон.
        Ошибкой помечается подстановка параметра, оцененного как неверный
        """
        errors: List[str] = []

        def repl(match: re.Match) -> str:
            name = match.group(1)
            param = self._parameters.get(name)
            if not param:
                return match.group(0)

            text = ""
            if getattr(param, "user_origin", None):
                text = param.user_origin.data.get("text", "")
                pre = getattr(param.user_origin, "pre_grade", {})
                if pre.get("score") != 1:
                    errors.append(
                        f"Параметр '{name}' предварительно неверен"
                    )
            elif getattr(param, "data", None):
                text = param.data.get("text", "")

            return self._normalize(text) if text else match.group(0)

        return self._RE_PARAM.sub(repl, line), errors

    def _validate_line(self, line: str, given_norm: str) -> Optional[str]:
        """
        Проверяет эталон.
        None, если всё ок, иначе текст ошибки
        """
        range_match = self._RE_RANGE.search(line)
        if not range_match:
            ok = self._normalize(line) in given_norm
            return None if ok else f"Не найден тезис: '{line}'"

        spec = range_match.group(1)
        start, end = line[: range_match.start()], line[range_match.end():]
        pattern = re.escape(start) + r"(\d+)" + re.escape(end)
        regex = re.compile(pattern, re.IGNORECASE)

        m = regex.search(given_norm)
        if not m:
            return f"Не найдено соответствие для тезиса: '{line}'"

        value = m.group(1)
        if not self._is_valid_range(value, spec):
            return f"Значение '{value}' не соответствует диапазону/вариантам '{spec}'"
        return None

    def _is_valid_range(self, given: str, specification: str) -> bool:
        """Проверка соответствия значения пользователя описанию (1-5 или 2|4|6)"""
        if not given.isdigit():
            return False
        num = int(given)

        if "|" in specification:
            return num in {int(x) for x in specification.split("|") if x.isdigit()}

        if m := re.fullmatch(r"(\d+)-(\d+)", specification):
            lo, hi = sorted(map(int, m.groups()))
            return lo <= num <= hi

        return True

    def _normalize(self, text: str) -> str:
        """Нормализация - нижний регистр + схлопывание пробелов"""
        return self._RE_SPACE.sub(" ", text.lower()).strip()
