import math
import re
from functools import lru_cache
from typing import Any, Tuple

from rapidfuzz import fuzz
from labstructanalyzer.models.dto.answer import GradeResult

RE_WORDS = re.compile(r'\w+')
RE_DIGITS = re.compile(r'-?\d+')


class FixedAnswerGrader:
    """Грейдер для ответов с фиксированным текстом"""

    DEFAULT_SIMILARITY_THRESHOLD = 92
    MIN_SIMILARITY_THRESHOLD = 70
    REDUCTION_FACTOR = 7

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
        given_digits = self._extract_digits(given)
        ref_digits = self._extract_digits(reference)
        given_words = self._extract_words(given)
        ref_words = self._extract_words(reference)

        if not self._digits_match(given_digits, ref_digits):
            return GradeResult(
                score=0,
                comment=(
                    f"Цифры не совпадают, извлечено из ответа: "
                    f"{'{}' if given_digits else ''}{'; '.join(given_digits) if given_digits else 'не найдены'}{'{}' if given_digits else ''}, "
                    f"из эталона: {'{}' if ref_digits else ''}{'; '.join(ref_digits) if ref_digits else 'не найдены'}{'{}' if ref_digits else ''}"
                ).format("'" if given_digits or ref_digits else "")
            )

        if self._exact_match(given_words, ref_words):
            return GradeResult(score=1, comment="Точное совпадение")

        if self._is_valid_prefix(given_words, ref_words):
            return GradeResult(score=1, comment="Является префиксом эталона")

        return self._fuzzy_evaluation(given_words, ref_words, reference)

    def _digits_match(self, given_digits: Tuple[str, ...], ref_digits: Tuple[str, ...]) -> bool:
        """
        Проверяет, совпадают ли все цифры в ответе и эталоне

        Args:
            given_digits: извлеченные цифры из ответа
            ref_digits: извлеченные цифры из эталона

        Returns:
            bool: True, если цифры совпадают
        """
        return set(ref_digits).issubset(set(given_digits))

    def _exact_match(self, given_words: Tuple[str, ...], ref_words: Tuple[str, ...]) -> bool:
        """
        Проверяет, полностью ли совпадают слова в ответе и эталоне

        Args:
            given_words: извлеченные слова из ответа
            ref_words: извлеченные слова из эталона

        Returns:
            bool: True, если слова совпадают
        """
        return given_words == ref_words

    def _is_valid_prefix(self, given_words: Tuple[str, ...], ref_words: Tuple[str, ...]) -> bool:
        """
        Проверяет, является ли ответ пользователя допустимым префиксом эталона

        Args:
            given_words: извлеченные слова из ответа
            ref_words: извлеченные слова из эталона

        Returns:
            bool: True, если ответ — допустимый префикс эталона
        """
        given_length, ref_length = len(given_words), len(ref_words)
        if ref_length == 0 or given_length == 0 or given_length < ref_length:
            return False
        for start in range(0, given_length - ref_length + 1):
            ok = True
            for i, ref_word in enumerate(ref_words):
                given_word = given_words[start + i]
                if not ref_word.startswith(given_word):
                    ok = False
                    break
            if ok:
                return True
        return False

    def _fuzzy_evaluation(
            self,
            given_words: Tuple[str, ...],
            ref_words: Tuple[str, ...],
            reference_original: str
    ) -> GradeResult:
        """
        Выполняет нечеткую проверку схожести между ответом и эталоном.
        Используется `fuzz.partial_ratio`. Порог схожести зависит от длины ответа

        Args:
            given_words: извлеченные слова из ответа
            ref_words: извлеченные слова из эталона
            reference_original: оригинальный необработанный эталонный текст

        Returns:
            GradeResult: результат оценки
        """
        text_len = len(given_words)
        threshold = self._calculate_similarity_threshold(text_len)

        similarity_score = fuzz.partial_ratio(
            ' '.join(given_words),
            ' '.join(ref_words),
        )

        if similarity_score >= threshold:
            return GradeResult(
                score=1,
                comment=f"Достаточное соответствие: текущее - {similarity_score:.2f}%, порог - {threshold:.2f}%"
            )

        return GradeResult(
            score=0,
            comment=(
                f"Недостаточное соответствие: текущее - {similarity_score:.2f}%, порог - {threshold:.2f}%, "
                f"эталон: '{reference_original}'"
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

    @staticmethod
    @lru_cache(maxsize=128)
    def _extract_digits(text: str) -> tuple[Any, ...]:
        """
        Извлекает все числовые фрагменты из текста

        Args:
            text: исходная строка

        Returns:
            tuple[Any, ...]: список найденных чисел
        """
        return tuple(RE_DIGITS.findall(text.lower()))

    @staticmethod
    @lru_cache(maxsize=128)
    def _extract_words(text: str) -> tuple[Any, ...]:
        """
        Извлекает слова из текста, приводит к нижнему регистру и кеширует результат (глобально)

        Args:
            text: исходная строка

        Returns:
            tuple[Any, ...]: список слов (токенов)
        """
        return tuple(RE_WORDS.findall(text.lower()))
