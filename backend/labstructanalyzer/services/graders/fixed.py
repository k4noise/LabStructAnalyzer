import re
from rapidfuzz import fuzz
from labstructanalyzer.models.dto.answer import GradeResult


class FixedAnswerGrader:
    """Грейдер для ответов с фиксированным текстом."""

    _RE_WORDS = re.compile(r'[a-zа-яёй]+')
    _RE_DIGITS = re.compile(r'\d+')

    def grade(self, given: str, reference: str) -> GradeResult:
        """Оценивает ответ на соответствие эталонному ответу

        Args:
            given: Ответ пользователя
            reference: Эталонный ответ

        Returns:
            Результат оценки
        """
        reference_words, reference_digits = self._split_alnum(reference)
        given_words, given_digits = self._split_alnum(given)

        if given_digits != reference_digits:
            return GradeResult(
                score=0,
                comment=f"Цифры не совпадают. Эталон: {reference}"
            )

        if given_words == reference_words:
            return GradeResult(score=1)

        if len(given_words) <= len(reference_words):
            for offset in range(len(reference_words) - len(given_words) + 1):
                if all(reference_words[offset + i].startswith(given_words[i])
                       for i in range(len(given_words))):
                    return GradeResult(score=1, comment="Верный префикс эталонного ответа")

        score = fuzz.ratio(given_words, reference_words)
        if score >= 90:
            return GradeResult(score=1)

        return GradeResult(
            score=0,
            comment=f"Порог схожести (90%) не достигнут: текущий {score}%, эталон {reference}"
        )

    def _split_alnum(self, answer: str) -> tuple[list[str], list[str]]:
        """Разделяет строку на списки слов и цифр

        Args:
            answer: Строка для разделения

        Returns:
            Кортеж, содержащий списки слов и цифр
        """
        answer = answer.lower()
        letters = self._RE_WORDS.findall(answer)
        digits = self._RE_DIGITS.findall(answer)
        return letters, digits
