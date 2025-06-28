import re
from functools import lru_cache
from typing import Dict, List, Tuple

from labstructanalyzer.schemas.answer import FullAnswerData, GradeResult
from labstructanalyzer.services.graders.range_spec import RangeSpec


class ParametrizedAnswerGrader:
    """
    Грейдер ответов с поддержкой:
      - подстановки параметров вида {param}
      - валидации значений по диапазонам / альтернативам внутри скобок []
      - поддержки литеральных скобок через двойной синтаксис [[...]]
    """

    _RE_PARAM = re.compile(r"\{([^}]+)}")
    _RE_RANGE = re.compile(r"\[(.*?)\]")
    _RE_SPACE = re.compile(r"\s+")
    _RE_LITERAL_ESCAPE = re.compile(r"\[\[(.+?)]]")
    _RE_PRESENCE_CHECK = re.compile(r'\{.*?\}|\[.*?\]')

    def __init__(self, parameters: Dict[str, FullAnswerData]):
        """
        Args:
            parameters: словарь параметров, подставляемых в {param}
        """
        self._parameters = parameters

    def is_processable(self, given: str, reference: str) -> bool:
        return bool(re.search(self._RE_PRESENCE_CHECK, reference))

    def grade(self, given: str, reference: str) -> GradeResult:
        """
        Основной метод оценки ответа пользователя

        Args:
            given: строка ответа пользователя
            reference: эталонная строка (или многострочный текст)

        Returns:
            GradeResult: содержит оценку (score 0/1) и комментарий
        """
        normalized = self._normalize(given)
        lines = [line.strip() for line in reference.splitlines() if line.strip()]

        if not lines:
            return GradeResult(score=1, comment="Эталон пуст")

        errors: List[str] = []
        pregraded_param_ids: List[str] = []

        for line in lines:
            line_errors, bad_params = self._check_line(line, normalized)
            errors.extend(line_errors)
            pregraded_param_ids.extend(bad_params)

        for parameter_name in pregraded_param_ids:
            errors.append(self._msg_param_invalid(parameter_name))

        return GradeResult(
            score=0 if errors else 1,
            comment="\n".join(errors) if errors else "Ответ верен",
            wrong_params=bad_params if bad_params else None
        )

    def _check_line(self, thesis: str, normalized_answer: str) -> Tuple[List[str], List[str]]:
        """
        Проверяет одну строку эталона (тезис) против нормализованного ответа

        Returns:
            Tuple:
              - список ошибок (если есть)
              - список id параметров с pre_grade=0
        """
        substituted, invalid_param_ids = self._substitute_params(thesis)
        substituted, literals = self._protect_literal_square_brackets(substituted)

        cursor = 0
        pattern = ""
        specs: List[Tuple[RangeSpec, str]] = []

        for match in self._RE_RANGE.finditer(substituted):
            start, end = match.span()
            if any(start >= l_start and end <= l_end for l_start, l_end in literals):
                # внутри [[...]] — игнорируем как диапазон
                continue
            pattern += re.escape(substituted[cursor:start])
            raw = match.group(1)
            spec = RangeSpec.from_raw(raw)
            specs.append((spec, raw))
            pattern += spec.regex_fragment()
            cursor = end

        pattern += re.escape(substituted[cursor:])
        if not specs:
            if self._normalize(substituted) in normalized_answer:
                return [], invalid_param_ids
            return [self._msg_literal_missing(substituted)], invalid_param_ids

        matcher = self._compile_pattern(pattern)
        match_obj = matcher.search(normalized_answer)
        if not match_obj:
            return [self._msg_regex_no_match(substituted)], invalid_param_ids

        value_errors: List[str] = []
        for idx, (spec, _) in enumerate(specs, start=1):
            value = match_obj.group(idx)
            if not spec.match(value):
                value_errors.append(self._msg_value_invalid(substituted, spec, value))

        return value_errors, invalid_param_ids

    def _substitute_params(self, line: str) -> Tuple[str, List[str]]:
        """
        Заменяет {param} в строке на реальные значения.
        Одновременно собирает имена параметров с pre_grade = 0

        Returns:
            Tuple:
              - строка после подстановки
              - список параметров, у которых pre_grade = 0
        """
        invalid_params: List[str] = []

        def replace(match: re.Match) -> str:
            name = match.group(1)
            param = self._parameters.get(name)
            if not param:
                return match.group(0)

            text_value = ""
            score = 1

            if hasattr(param, "user_origin"):
                text_value = param.user_origin.data.get("text") or ""
                score = param.user_origin.pre_grade.get("score", 1)

            if score == 0:
                invalid_params.append(name)

            return self._normalize(text_value or match.group(0))

        substituted = self._RE_PARAM.sub(replace, line)
        return substituted, invalid_params

    def _protect_literal_square_brackets(self, text: str) -> Tuple[str, List[Tuple[int, int]]]:
        """
        Находит в строке все [[...]] и возвращает:
          - строку без двойных скобок
          - список координат, где были защищённые блоки (для исключения из range-парса)

        Args:
            text: строка с литеральными блоками внутри [[...]]

        Returns:
            (текст с заменами, список диапазонов [(start, end)])
        """
        result = ""
        protected_ranges: List[Tuple[int, int]] = []
        last = 0

        for match in self._RE_LITERAL_ESCAPE.finditer(text):
            start, end = match.span()
            content = match.group(1)
            result += text[last:start] + "[" + content + "]"
            protected_ranges.append((len(result) - len(content) - 2, len(result)))  # скобки включительно
            last = end

        result += text[last:]
        return result, protected_ranges

    def _msg_literal_missing(self, thesis: str) -> str:
        return f"Не найден обязательный фрагмент: '{thesis}'"

    def _msg_regex_no_match(self, thesis: str) -> str:
        return f"Не найдено соответствие для тезиса: '{thesis}'"

    def _msg_value_invalid(self, thesis: str, spec: RangeSpec, value: str) -> str:
        values = spec.values
        if spec.is_numeric and not spec.is_mixed and len(spec.parts) == 1 and isinstance(spec.parts[0], tuple):
            start, end = spec.parts[0]
            return f"В тезисе '{thesis}' значение '{value}' не попадает в диапазон [{start}–{end}]"
        if spec.is_numeric and not spec.is_mixed:
            return f"В тезисе '{thesis}' значение '{value}' не входит в множество {values}"
        return f"В тезисе '{thesis}' значение '{value}' не соответствует допустимым альтернативам {values}"

    def _msg_param_invalid(self, param_name: str) -> str:
        return f"Параметр '{param_name}' предварительно неверен (score=0)"

    @staticmethod
    @lru_cache(maxsize=256)
    def _normalize(text: str) -> str:
        """
        Приводит текст к нижнему регистру и удаляет лишние пробелы
        """
        return ParametrizedAnswerGrader._RE_SPACE.sub(" ", text.lower()).strip()

    @staticmethod
    @lru_cache(maxsize=512)
    def _compile_pattern(pattern: str) -> re.Pattern:
        """
        Компилирует и кэширует регулярное выражение без повторной обработки
        """
        return re.compile(pattern, re.IGNORECASE)
