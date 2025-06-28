import re
from functools import lru_cache

from rapidfuzz import fuzz
from labstructanalyzer.schemas.answer import GradeResult

RE_WORDS = re.compile(r"[\w'-]+")
RE_DIGITS = re.compile(r'-?\d+')


class FixedAnswerGrader:
    """
    Грейдер для оценки кратких текстовых ответов с нечетким сравнением

    Особенности:
      - Проверка наличия всех необходимых чисел
      - Поддержка опечаток
      - Поддержка сокращений по префиксу
      - Толерантность к лишним словам в ответе при сохранении порядка ключевых слов
      - Толерантность к неполным ответам при сохранении последовательности ключевых слов
    """

    DEFAULT_SIMILARITY_THRESHOLD = 80
    WORDS_LENGTH_THRESHOLD = 10
    WORD_COUNT_THRESHOLD = 2
    MAX_PROCESSABLE_LENGTH = 35

    def is_processable(self, given: str, reference: str) -> bool:
        if max(len(reference), len(given)) > self.MAX_PROCESSABLE_LENGTH:
            return False

        len_diff_ok = abs(len(reference) - len(given)) < self.WORDS_LENGTH_THRESHOLD

        given_words_count = len(self._extract_words(given))
        ref_words_count = len(self._extract_words(reference))
        word_count_diff_ok = abs(ref_words_count - given_words_count) <= self.WORD_COUNT_THRESHOLD

        return len_diff_ok and word_count_diff_ok

    def grade(self, given: str, reference: str) -> GradeResult:
        """
        Анализирует ответ пользователя по сравнению с эталоном

        Args:
            given: Ответ пользователя
            reference: Эталонный ответ

        Returns:
            GradeResult: Объект с оценкой и комментарием
        """
        given_digits_set = set(self._extract_digits(given))
        ref_digits_set = set(self._extract_digits(reference))
        missing_digits = ref_digits_set - given_digits_set

        if missing_digits:
            missing = "; ".join(list(missing_digits))
            return GradeResult(
                score=0,
                comment=f"Отсутствуют требуемые числа: [{missing}]"
            )

        given_words = self._extract_words(given)
        ref_words = self._extract_words(reference)

        if given_words == ref_words:
            return GradeResult(1, "Полное совпадение")

        if self._is_strict_prefix(given_words, ref_words):
            return GradeResult(1, "Допустимое сокращение")

        if self._is_fuzzy_subsequence(subsequence=ref_words, main_sequence=given_words):
            return GradeResult(1, "С опечатками или лишними словами")

        if self._is_fuzzy_subsequence(subsequence=given_words, main_sequence=ref_words):
            return GradeResult(1, "Неполный, но последовательный ответ")

        return GradeResult(0, "Слова или их порядок не совпадают с эталоном")

    @staticmethod
    @lru_cache(maxsize=128)
    def _extract_digits(text: str) -> tuple[str, ...]:
        """
        Извлекает из текста все целые числа (включая отрицательные)

        Returns:
            Кортеж найденных числовых строк
        """
        return tuple(RE_DIGITS.findall(text))

    @staticmethod
    @lru_cache(maxsize=128)
    def _extract_words(text: str) -> tuple[str, ...]:
        """
        Извлекает все слова из текста, приводя их к нижнему регистру

        Returns:
            Кортеж слов в нижнем регистре
        """
        return tuple(RE_WORDS.findall(text.lower()))

    def _words_match(self, word1: str, word2: str) -> bool:
        """
        Сравнивает два слова, используя нечеткую проверку

        Слова считаются совпадающими, если одно является префиксом другого или
        их сходство по rapidfuzz.ratio превышает порог по умолчанию

        Returns:
            True, если слова удовлетворяют условиям совпадения, иначе False
        """
        return (word1.startswith(word2) or
                word2.startswith(word1) or
                fuzz.ratio(word1, word2) >= self.DEFAULT_SIMILARITY_THRESHOLD)

    @staticmethod
    def _is_strict_prefix(shorter_seq: tuple[str, ...], longer_seq: tuple[str, ...]) -> bool:
        """
        Проверяет, является ли shorter_seq строгим пословным префиксом longer_seq.
        Каждый элемент shorter_seq должен быть префиксом соответствующего элемента longer_seq

        Args:
            shorter_seq: Потенциальная сокращённая последовательность
            longer_seq: Полная последовательность

        Returns:
             True, если shorter_seq действительно является префиксом longer_seq
        """
        if len(shorter_seq) > len(longer_seq):
            return False
        return all(long_w.startswith(short_w) for short_w, long_w in zip(shorter_seq, longer_seq))

    def _is_fuzzy_subsequence(self, subsequence: tuple[str, ...], main_sequence: tuple[str, ...]) -> bool:
        """
        Определяет, является ли subsequence нечеткой подпоследовательностью main_sequence.
        Все слова из subsequence должны встречаться в main_sequence в том же порядке.
        Сравнение производится с использованием нечеткого сравнения

        Args:
            subsequence: Потенциальная подпоследовательность
            main_sequence: Основная последовательность для поиска

        Returns:
            True, если subsequence обнаружена в main_sequence, иначе False
        """
        main_iter = iter(main_sequence)
        for sub_word in subsequence:
            if not any(self._words_match(sub_word, main_word) for main_word in main_iter):
                return False
        return True
