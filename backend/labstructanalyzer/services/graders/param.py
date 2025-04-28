import re
from typing import Dict, List, Tuple, Optional
from labstructanalyzer.models.dto.answer import FullAnswerData, GradeResult


class ParametrizedAnswerGrader:
    _RE_PARAM_PLACEHOLDER = re.compile(r'\{([^}]+)}')
    _RE_RANGE_PLACEHOLDER = re.compile(r'\[(.*?)]')
    _RE_SINGLE_SPACE = re.compile(r'\s+')

    def __init__(self, parameters: Dict[str, FullAnswerData]):
        self._parameters = parameters

    def grade(self, given_answer: str, reference_answer: str) -> GradeResult:
        validation_errors: List[str] = []
        reference_answer_lines = [line.strip() for line in reference_answer.splitlines() if line.strip()]
        if not reference_answer_lines:
            return GradeResult(score=1)

        normalized_given_answer = self._normalize_text(given_answer)

        for reference_answer_line in reference_answer_lines:
            substituted_line, parameter_errors = self._replace_parameter_placeholders(reference_answer_line)
            validation_errors.extend(parameter_errors)

            is_valid, error = self._check_answer_line(substituted_line, normalized_given_answer)
            if not is_valid:
                if error:
                    validation_errors.append(error)

        if validation_errors:
            error_message = "\n".join(filter(None, validation_errors))
            return GradeResult(score=0, comment=error_message if error_message else None)
        return GradeResult(score=1)

    def _replace_parameter_placeholders(self, reference_answer_line: str) -> Tuple[str, List[str]]:
        errors: List[str] = []
        result = reference_answer_line

        for parameter_name in self._RE_PARAM_PLACEHOLDER.findall(reference_answer_line):
            parameter_data = self._parameters.get(parameter_name)

            if not parameter_data:
                continue

            parameter_text = ""
            if hasattr(parameter_data, 'user_origin') and parameter_data.user_origin:
                parameter_text = parameter_data.user_origin.data.get("text", "")
                pre_grade = getattr(parameter_data.user_origin, 'pre_grade', {})
                if pre_grade.get("score") != 1:
                    error_msg = pre_grade.get('comment', 'Неизвестная ошибка')
                    errors.append(f"Параметр '{parameter_name}' имеет невалидный pre_grade: {error_msg}")
            elif hasattr(parameter_data, 'data') and parameter_data.data:
                parameter_text = parameter_data.data.get("text", "")

            if not parameter_text:
                continue

            normalized_parameter = self._normalize_text(parameter_text)
            result = result.replace(f"{{{parameter_name}}}", normalized_parameter)

        return result, errors

    def _check_answer_line(self, substituted_line: str, normalized_given_answer: str) -> Tuple[bool, Optional[str]]:
        range_match = self._RE_RANGE_PLACEHOLDER.search(substituted_line)
        if not range_match:
            return self._check_exact_match(substituted_line, normalized_given_answer)
        return self._check_range_match(substituted_line, normalized_given_answer)

    def _check_exact_match(self, substituted_line: str, normalized_given_answer: str) -> Tuple[bool, Optional[str]]:
        normalized_substituted_line = self._normalize_text(substituted_line)
        return normalized_substituted_line in normalized_given_answer, None

    def _check_range_match(self, substituted_line: str, normalized_given_answer: str) -> Tuple[bool, Optional[str]]:
        before_range = substituted_line[:self._RE_RANGE_PLACEHOLDER.search(substituted_line).start()]
        range_specification = self._RE_RANGE_PLACEHOLDER.search(substituted_line).group(1)
        after_range = substituted_line[self._RE_RANGE_PLACEHOLDER.search(substituted_line).end():]

        pattern = re.escape(before_range) + r'(\d+)' + re.escape(after_range)
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return False, f"Ошибка в формате тезиса: {substituted_line}"

        match = regex.search(normalized_given_answer)
        if not match:
            return False, f"Не найдено соответствие для тезиса: {substituted_line}"

        extracted_value = match.group(1).strip()
        if not extracted_value:
            return False, f"Пустое значение для диапазона '{range_specification}'"

        if self._is_range_specification_valid(range_specification):
            valid, error = self._check_range_validity(extracted_value, range_specification)
            if not valid:
                return False, error or f"Значение '{extracted_value}' не соответствует диапазону '{range_specification}'"

        return True, None

    def _normalize_text(self, text: str) -> str:
        return self._RE_SINGLE_SPACE.sub(' ', text.lower()).strip()

    def _check_range_validity(self, extracted_value: str, range_specification: str) -> Tuple[bool, Optional[str]]:
        if not extracted_value.isdigit():
            return False, f"Значение '{extracted_value}' не является числом"

        num = int(extracted_value)

        if '|' in range_specification:
            options = {int(opt) for opt in range_specification.split('|') if opt.isdigit()}
            if num not in options:
                return False, f"Значение '{extracted_value}' не соответствует вариантам: {options}"
            return True, None

        if match := re.fullmatch(r'(\d+)-(\d+)', range_specification):
            min_val, max_val = sorted(map(int, match.groups()))
            if not (min_val <= num <= max_val):
                return False, f"Значение '{extracted_value}' не входит в диапазон {min_val}-{max_val}"
            return True, None

        return True, None

    def _is_range_specification_valid(self, range_specification: str) -> bool:
        return '|' in range_specification or re.fullmatch(r'\d+-\d+', range_specification)
