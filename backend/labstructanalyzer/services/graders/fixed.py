import math
import re
from typing import List

from rapidfuzz import fuzz
from labstructanalyzer.models.dto.answer import GradeResult


class FixedAnswerGrader:
    """Грейдер для ответов с фиксированным текстом"""

    _RE_WORDS = re.compile(r'\w+')
    _RE_DIGITS = re.compile(r'\d+')

    DEFAULT_SIMILARITY_THRESHOLD = 92
    MIN_SIMILARITY_THRESHOLD = 70
    REDUCTION_FACTOR = 2

    def grade(self, given: str, reference: str) -> GradeResult:
        """
        Оценивает ответ на соответствие эталонному ответу

        Проверка происходит по этапам:
        1. Совпадают ли извлечённые цифры
        2. Полное совпадение слов
        3. Проверка на корректный префикс
        4. Оценка нечеткой схожести

        Args:
            given: ответ пользователя
            reference: эталонный ответ

        Returns:
            GradeResult: оценка за ответ (1 — верно; 0 — неверно)
        """
        if not self._digits_match(given, reference):
            return GradeResult(score=0, comment=f"Цифры не совпадают, эталон '{reference}'")

        if self._exact_match(given, reference):
            return GradeResult(score=1)

        if self._is_valid_prefix(given, reference):
            return GradeResult(score=1, comment="Верный префикс эталонного ответа")

        return self._fuzzy_evaluation(given, reference)

    def _digits_match(self, given: str, reference: str) -> bool:
        """
        Проверяет, совпадают ли все цифры в ответе и эталоне

        Args:
            given: ответ пользователя
            reference: эталонный ответ

        Returns:
            bool: True, если цифры совпадают
        """
        return self._extract_digits(given) == self._extract_digits(reference)

    def _exact_match(self, given: str, reference: str) -> bool:
        """
        Проверяет, полностью ли совпадают слова в ответе и эталоне

        Args:
            given: ответ пользователя
            reference: эталонный ответ

        Returns:
            bool: True, если слова совпадают
        """
        return self._extract_words(given) == self._extract_words(reference)

    def _is_valid_prefix(self, given: str, reference: str) -> bool:
        """
        Проверяет, является ли ответ пользователя допустимым префиксом эталона

        Args:
            given: ответ пользователя
            reference: эталонный ответ

        Returns:
            bool: True, если ответ — допустимый префикс эталона
        """
        given_words = self._extract_words(given)
        ref_words = self._extract_words(reference)

        if len(given_words) > len(ref_words):
            return False

        for offset in range(len(ref_words) - len(given_words) + 1):
            if all(
                    ref_words[offset + i].startswith(given_words[i])
                    for i in range(len(given_words))
            ):
                return True

        return False

    def _fuzzy_evaluation(self, given: str, reference: str) -> GradeResult:
        """
        Выполняет нечеткую проверку схожести между ответом и эталоном.
        Используется `fuzz.partial_ratio`. Порог схожести зависит от длины ответа

        Args:
            given: ответ пользователя
            reference: эталонный ответ

        Returns:
            GradeResult: результат оценки
        """
        given_words = self._extract_words(given)
        ref_words = self._extract_words(reference)

        if not given_words or not ref_words:
            return GradeResult(score=0, comment="Пустой ответ или эталон после обработки")

        text_len = len(given_words)
        threshold = self._calculate_similarity_threshold(text_len)

        similarity_score = fuzz.partial_ratio(
            ' '.join(given_words),
            ' '.join(ref_words),
        )

        if similarity_score >= threshold:
            return GradeResult(score=1)

        return GradeResult(
            score=0,
            comment=(
                f"Порог схожести ({threshold:.2f}%) не достигнут: текущий {similarity_score:.2f}%, "
                f"эталон '{reference}'"
            )
        )

    def _calculate_similarity_threshold(self, word_count: int) -> float:
        """
        Вычисляет динамический порог схожести на основе количества слов

        Args:
            word_count: количество слов в ответе пользователя

        Returns:
            float: требуемый % схожести
        """
        threshold = self.DEFAULT_SIMILARITY_THRESHOLD - (self.REDUCTION_FACTOR * math.log(word_count + 1))
        return max(self.MIN_SIMILARITY_THRESHOLD, threshold)

    def _extract_digits(self, text: str) -> List[str]:
        """
        Извлекает все числовые фрагменты из текста

        Args:
            text: исходная строка

        Returns:
            List[str]: список найденных чисел
        """
        return self._RE_DIGITS.findall(text.lower())

    def _extract_words(self, text: str) -> List[str]:
        """
        Извлекает слова из текста, приводит к нижнему регистру

        Args:
            text: исходная строка

        Returns:
            List[str]: список слов (токенов)
        """
        return self._RE_WORDS.findall(text.lower())
