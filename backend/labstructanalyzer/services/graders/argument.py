import re
from functools import lru_cache
from typing import List, Optional

import numpy as np
from natasha import NewsEmbedding
from pymorphy2 import MorphAnalyzer

from labstructanalyzer.models.dto.answer import GradeResult


class ArgumentAnswerGrader:
    """
    Грейдер для оценивания ответов-рассуждений.

    Оценивает, насколько тезисы преподавателя отражены
    в ответе пользователя, на основе семантической близости предложений
    """

    POS_WEIGHTS = {
        'NOUN': 1.0,
        'VERB': 0.8,
        'ADJF': 0.6,
        'NUMR': 0.8,
    }

    DEFAULT_WEIGHT = 0.3
    SIMILARITY_THRESHOLD = 0.85

    def __init__(self):
        self.morph = MorphAnalyzer()
        self.word_vectors = NewsEmbedding()
        self.vector_size = 300

    def grade(self, given: str, reference: str) -> GradeResult:
        """
        Основной метод оценки ответа пользователя

        Args:
            given: строка ответа пользователя
            reference: эталонная строка (или многострочный текст)

        Returns:
            GradeResult: содержит оценку (score 0/1) и комментарий
        """
        user_sentences = self._split_sentences(given)
        reference_theses = self._split_sentences(reference)

        if not reference_theses:
            return GradeResult(score=1, comment="Эталон пуст")

        if not user_sentences:
            return GradeResult(score=0)

        theses_vectors = [self._compute_sentence_vector(s) for s in reference_theses]
        user_vectors = [self._compute_sentence_vector(s) for s in user_sentences]

        scores = self._match_theses(theses_vectors, user_vectors)
        score = sum(scores) / len(scores)

        comment = self._generate_comment(reference_theses, scores) if score < 1 else None
        return GradeResult(score=score, comment=comment)

    def _match_theses(self, ref_vecs: List[np.ndarray], user_vecs: List[np.ndarray]) -> List[int]:
        """
        Для каждого тезиса выбирает максимальное сходство с любым предложением ответа

        Returns:
            Список 0/1 (тезис найден/не найден)
        """
        return [
            int(max(self._cosine_similarity(ref_vec, user_vec) for user_vec in user_vecs) >= self.SIMILARITY_THRESHOLD)
            for ref_vec in ref_vecs
        ]

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Косинусная близость между двумя векторами. Нормализуется в [0..1]

        Returns:
            float: округлённая близость
        """
        if v1.shape != v2.shape or not np.any(v1) or not np.any(v2):
            return 0.0

        raw_score = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        return round((raw_score + 1) / 2, 3)

    def _generate_comment(self, theses: List[str], match_mask: List[int]) -> str:
        """
        Формирует строку вида: "Тезисы не найдены: <список>"

        Returns:
            str | None
        """
        missed = [t for t, flag in zip(theses, match_mask) if flag == 0]
        return f"Тезисы не найдены: {'; '.join(missed)}" if missed else None

    def _compute_sentence_vector(self, sentence: str) -> np.ndarray:
        """
        Вычисляет взвешенный sentence-vector из слов в предложении

        Returns:
            np.ndarray: вектор длины vector_size или нулевой
        """
        tokens = self._tokenize(sentence)
        if not tokens:
            return np.zeros(self.vector_size)

        vectors, weights = [], []

        for token in tokens:
            norm = self._lemmatize(token)
            weight = self._get_pos_weight(norm)
            vector = self._get_embedding(norm)

            if vector is not None:
                vectors.append(vector)
                weights.append(weight)

        if not vectors:
            return np.zeros(self.vector_size)

        weights_arr = np.array(weights)
        matrix = np.array(vectors) * weights_arr[:, None]
        return np.sum(matrix, axis=0) / np.sum(weights_arr)

    def _get_embedding(self, word: str) -> Optional[np.ndarray]:
        """
        Возвращает эмбеддинг слова из модели, если найден

        Returns:
            np.ndarray | None
        """
        return self.word_vectors.get(word.lower())

    def _get_pos_weight(self, word: str) -> float:
        """
        Вычисляет вес слова на основе его части речи
        """
        parsed = self.morph.parse(word)[0]
        pos = parsed.tag.POS
        return self.POS_WEIGHTS.get(pos, self.DEFAULT_WEIGHT)

    @lru_cache(maxsize=4096)
    def _lemmatize(self, word: str) -> str:
        """
        Возвращает нормальную форму слова (лемматизация)
        """
        return self.morph.parse(word)[0].normal_form

    def _normalize_text(self, text: str) -> str:
        """
        Приводит текст к lowercase, удаляет лишние символы, нормализует пробелы
        """
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.lower()

    def _tokenize(self, text: str) -> List[str]:
        """
        Делает токенизацию и нормализацию текста

        Returns:
            Список "слов"
        """
        norm = self._normalize_text(text)
        return re.findall(r'\w+', norm)

    def _split_sentences(self, text: str) -> List[str]:
        """
        Делит текст на предложения по знакам [.?!]

        Returns:
            Список непустых предложений
        """
        return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
