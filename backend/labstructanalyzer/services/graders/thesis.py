import os.path
from functools import lru_cache
from typing import List

import numpy as np
from compress_fasttext import CompressedFastTextKeyedVectors
from pymorphy3 import MorphAnalyzer
from razdel import sentenize, tokenize

from labstructanalyzer.configs.config import BASE_PROJECT_DIR
from labstructanalyzer.models.dto.answer import GradeResult


@lru_cache(maxsize=1)
def load_fasttext_model() -> CompressedFastTextKeyedVectors:
    """
    Загружает сжатую модель FastText из файла

    Returns:
        Загруженная сжатая модель векторов слов
    """
    return CompressedFastTextKeyedVectors.load(
        os.path.join(BASE_PROJECT_DIR, "labstructanalyzer/assets", "geowac_tokens_sg_300_5_2020-100K-20K-100.bin")
    )


class ThesisAnswerGrader:
    """
    Грейдер для оценивания ответов-рассуждений.
    Оценивает, насколько тезисы преподавателя отражены в ответе пользователя,
    на основе семантической близости предложений
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
        self.word_vectors = load_fasttext_model()
        self.vector_size = self.word_vectors.vector_size

    def is_processable(self, given: str, reference: str) -> bool:
        return len(given) >= 40 or len(list(sentenize(reference.replace("\n", ".")))) >= 2

    def grade(self, given: str, reference: str) -> GradeResult:
        """
        Основной метод оценки ответа пользователя

        Args:
            given: строка ответа пользователя
            reference: эталонная строка (или многострочный текст)

        Returns:
            GradeResult: Объект с оценкой (score от 0 до 1) и комментарием

        Raises:
            ValueError: Если модель не загружена или текст некорректен
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

    def _match_theses(self, reference_theses_vectors: List[np.ndarray], user_answer_vectors: List[np.ndarray]) -> List[
        int]:
        """
        Вычисляет косинусное сходство между векторами предложений.
        Предполагается, что векторы уже нормализованы

        Returns:
            Список 0/1 (тезис найден/не найден)
        """
        if not reference_theses_vectors or not user_answer_vectors:
            return [0] * len(reference_theses_vectors)

        scores = []
        for ref_vec in reference_theses_vectors:
            similarities = []
            for user_vec in user_answer_vectors:
                if len(ref_vec) > 0 and len(user_vec) > 0:
                    similarities.append(self._cosine_similarity(ref_vec, user_vec))
            if similarities:
                max_score = max(similarities)
                scores.append(int(max_score >= self.SIMILARITY_THRESHOLD))
            else:
                scores.append(0)
        return scores

    def _cosine_similarity(self, reference_theses_vectors: np.ndarray, user_answer_vectors: np.ndarray) -> float:
        """
        Косинусная близость между двумя векторами. Нормализуется в [0..1]

        Returns:
            Список значений 0/1, где 1 - тезис найден, 0 - не найден

        Raises:
            ValueError: Если входные списки пусты
        """
        if len(reference_theses_vectors) == 0 or len(user_answer_vectors) == 0 or np.linalg.norm(
                reference_theses_vectors) == 0 or np.linalg.norm(user_answer_vectors) == 0:
            return 0.0
        dot_product = np.dot(reference_theses_vectors, user_answer_vectors)
        return dot_product / (np.linalg.norm(reference_theses_vectors) * np.linalg.norm(user_answer_vectors))

    def _generate_comment(self, theses: List[str], match_mask: List[int]) -> str:
        """
        Формирует строку вида: "Тезисы не найдены: <список>"

        Returns:
            str: Строка с перечнем несоответствующих тезисов, или None, если все совпали.
        """
        missed = [thesis for thesis, flag in zip(theses, match_mask) if flag == 0]
        return f"Тезисы не найдены: {'; '.join(missed)}" if missed else None

    def _compute_sentence_vector(self, sentence: str) -> np.ndarray:
        """
        Вычисляет взвешенный и нормализованный вектор предложения

        Returns:
            Нормализованный вектор предложения или нулевой вектор, если предложение пустое
        """
        tokens = self._tokenize(sentence)
        if not tokens:
            return np.zeros(self.vector_size)

        vectors = []
        weights = []

        for token in tokens:
            word = self._lemmatize(token).lower()
            try:
                vec = self.word_vectors.get_vector(word)
                vectors.append(vec)
                weights.append(self._get_pos_weight(word))
            except (KeyError, AttributeError):
                continue

        if not vectors:
            return np.zeros(self.vector_size)

        avg = np.average(vectors, axis=0, weights=weights)
        norm = np.linalg.norm(avg)
        if norm == 0:
            return np.zeros(self.vector_size)
        return avg / norm

    def _get_pos_weight(self, word: str) -> float:
        """
        Возвращает вес слова на основе его части речи

        Args:
           Лемматизированное слово

        Returns:
            Вес слова (из POS_WEIGHTS или DEFAULT_WEIGHT)
        """
        parsed = self.morph.parse(word)[0]
        pos = parsed.tag.POS
        return self.POS_WEIGHTS.get(pos, self.DEFAULT_WEIGHT)

    @lru_cache(maxsize=4096)
    def _lemmatize(self, word: str) -> str:
        """
        Лемматизирует слово

        Returns:
            Нормальная форма слова
        """
        return self.morph.parse(word.lower())[0].normal_form

    def _tokenize(self, text: str) -> List[str]:
        """
        Токенизирует текст и фильтрует токены

        Returns:
            Список отфильтрованных токенов (только буквы и числа)
        """
        return [token.text for token in tokenize(text) if token.text.isalnum()]

    def _split_sentences(self, text: str) -> List[str]:
        """
        Разделяет текст на предложения

        Returns:
            Список непустых предложений
        """
        return [sent.text.strip() for sent in sentenize(text) if sent.text.strip()]
