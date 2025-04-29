from typing import List
from natasha import NewsEmbedding
from pymorphy2 import MorphAnalyzer
import numpy as np
import re
from functools import lru_cache

from labstructanalyzer.models.dto.answer import GradeResult


class ArgumentAnswerGrader:
    """Проверяет ответы-рассуждения, выполняя оценку наличия каждого тезиса преподавателя в ответе"""
    POS_WEIGHTS = {
        'NOUN': 1.0,
        'VERB': 0.8,
        'ADJF': 0.6,
        'NUMR': 0.8,
    }
    DEFAULT_WEIGHT = 0.3

    def __init__(self):
        self.morph = MorphAnalyzer()
        self.word_vectors = NewsEmbedding()
        self.vector_size = 300

    def grade(self, given: str, reference: str) -> GradeResult:
        """Оценивает ответ на соответствие эталонному ответу.

         Args:
             given: Ответ пользователя
             reference: Эталонный ответ

         Returns:
             Результат оценки
         """
        reference_theses_raw = self._split_into_sentences_raw(reference)
        answer_sentences_raw = self._split_into_sentences_raw(given)

        if not reference_theses_raw:
            return GradeResult(score=1, comment="Эталон пуст")
        if not answer_sentences_raw:
            return GradeResult(score=0)

        reference_theses = [self._preprocess_text(s) for s in reference_theses_raw]
        answer_sentences = [self._preprocess_text(s) for s in answer_sentences_raw]

        thesis_scores = [
            1 if max(
                self._cosine_similarity(
                    self._get_vector(thesis),
                    self._get_vector(sentence)
                ) for sentence in answer_sentences
            ) >= 0.85 else 0
            for thesis in reference_theses
        ]

        score = sum(thesis_scores) / len(reference_theses)
        comment = self._make_comment(reference_theses_raw, thesis_scores) if score != 1 else None
        return GradeResult(score=score, comment=comment)

    def _make_comment(self, reference_theses_raw: List[str], thesis_scores: List[int]) -> str:
        """
        Формирует строку-комментарий со списком ненайденных тезисов

        Args:
            reference_theses_raw: исходные тезисы преподавателя
            thesis_scores: список 0/1, совпал ли тезис

        Returns:
            Строка вида «Тезисы не найдены: …» или None, если все найдены
        """
        missed = [thesis for thesis, score in zip(reference_theses_raw, thesis_scores) if score == 0]
        return f"Тезисы не найдены: {'; '.join(missed)}" if missed else None

    @lru_cache(maxsize=10000)
    def _normalize_word(self, word: str) -> str:
        """Лемматизация слова и его кеширование"""
        return self.morph.parse(word)[0].normal_form

    def _preprocess_text(self, text: str) -> str:
        """
        Удаляет лишние символы, делает текст «чистым» для токенизации -
        - убирает двойные пробелы;
        - сохраняет только кириллицу, пробелы и базовую пунктуацию;
        - приводит к нижнему регистру.
        """
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.lower()

    def _tokenize(self, text: str) -> List[str]:
        """
        Делит текст на слова

        Returns:
            Список токенов-слов
        """
        return re.findall(r'\w+', self._preprocess_text(text))

    def _split_into_sentences_raw(self, text: str) -> List[str]:
        """
        Делит входную строку по последовательностям символов
        «.», «!» или «?» (один или несколько подряд)

        Returns: Cписок предложений без ведущих/конечных пробелов,
                 пустые строки отфильтровываются.
        """
        return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Косинусная близость двух векторов со сжатием диапазона.

        Если размерности различаются или один из векторов нулевой – возвращается 0.0.
        Иначе рассчитывается обычная cosine similarity (в диапазоне [-1; 1])
        и переносится в [0; 1] путём `(sim + 1) / 2`.

        Результат округляется до тысячных

        Returns: Нормализованная величина [0..1]
        """
        if vec1.shape != vec2.shape or not np.any(vec1) or not np.any(vec2):
            return 0.0
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return round(float((similarity + 1) / 2), 3)

    def _get_vector(self, text: str) -> np.ndarray:
        """
        Строит взвешенный sentence-vector для указанного текста

        Шаги:
            1. Токенизация и лемматизация каждого слова.
            2. Получение word2vec-эмбеддинга из NewsEmbedding.
            3. Взвешивание каждого вектора согласно части речи
               (POS_WEIGHTS) или DEFAULT_WEIGHT.
            4. Возврат взвешенного среднего.
               Если ни одного эмбеддинга получить не удалось —
               возвращается нулевой вектор нужной размерности.

        Returns: Вектор длины `self.vector_size`.
        """
        words = self._tokenize(text)
        if not words:
            return np.zeros(self.vector_size)

        vectors, weights = [], []
        for word in words:
            parsed = self.morph.parse(word)[0]
            pos = parsed.tag.POS
            weight = self.POS_WEIGHTS.get(pos, self.DEFAULT_WEIGHT)
            word_vec = self.word_vectors.get(word.lower())
            if word_vec is not None:
                vectors.append(word_vec)
                weights.append(weight)

        if not vectors:
            return np.zeros(self.vector_size)

        weights = np.array(weights)
        weighted_vectors = np.array(vectors) * weights[:, np.newaxis]
        return np.sum(weighted_vectors, axis=0) / np.sum(weights)
