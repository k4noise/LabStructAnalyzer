import os
from collections.abc import Sequence
from typing import Final

import numpy as np
import onnxruntime as ort
from razdel import sentenize
from scipy.optimize import linear_sum_assignment
from transformers import AutoTokenizer

from labstructanalyzer.configs.config import ONNX_MODEL_DIR
from labstructanalyzer.schemas.answer import GradeResult

SIMILARITY_THRESHOLD: Final[float] = 0.78
MIN_SENTENCE_LENGTH: Final[int] = 10
MIN_TOKEN_COUNT: Final[int] = 3
MAX_SEQUENCE_LENGTH: Final[int] = 128
VECTOR_DIMENSION: Final[int] = 312
SIMILARITY_CLOSE_THRESHOLD: Final[float] = 0.5
MAX_COMMENT_ITEMS: Final[int] = 10


def load_onnx_session(model_dir: str) -> ort.InferenceSession:
    """
    Загружает ONNX Runtime сессию для модели с именем model.onnx
    из относительного пути директории
    """
    model_path = os.path.join(model_dir, "model.onnx")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"ONNX модель не найдена в указанном пути: {model_path}")

    return ort.InferenceSession(model_path)


def load_tokenizer(model_dir: str) -> AutoTokenizer:
    """Загружает токенизатор из указанного относительного пути директории"""
    return AutoTokenizer.from_pretrained(model_dir)


class ThesisAnswerGrader:
    """Оценщик студенческих ответов на основе семантического сравнения с эталоном"""

    def __init__(self, model_dir: str = ONNX_MODEL_DIR):
        self.session = load_onnx_session(model_dir)
        self.tokenizer = load_tokenizer(model_dir)
        self.vector_size = VECTOR_DIMENSION

    def is_processable(self, given: str, reference: str) -> bool:
        """Проверяет, достаточно ли содержательны тексты для обработки"""
        ref_sents = len(list(sentenize(reference.replace("\n", " "))))
        return len(given.strip()) >= MIN_SENTENCE_LENGTH * 4 or ref_sents >= 2

    def grade(self, given: str, reference: str) -> GradeResult:
        """
        Оценивает ответ студента относительно эталона.
        Возвращает результат оценки с баллом [0.0, 1.0] и опциональным комментарием
        """
        given = given.strip()
        reference = reference.strip()

        user_sentences = self._split_sentences(given)
        reference_theses = self._split_sentences(reference)

        if not reference_theses:
            raise ValueError(
                "Эталонный текст пустой или состоит только из пробелов/переносов"
            )

        if not user_sentences:
            return GradeResult(score=0.0, comment="Ответ пустой")

        ref_vectors = self._compute_vectors_batch(reference_theses)
        user_vectors = self._compute_vectors_batch(user_sentences)

        match_scores = self._compute_best_matches(ref_vectors, user_vectors)
        score = np.mean(match_scores)

        comment = None
        if score < 1.0:
            comment = self._generate_comment(
                reference_theses=reference_theses,
                user_sentences=user_sentences,
                ref_vectors=ref_vectors,
                user_vectors=user_vectors,
                match_scores=match_scores,
            )

        return GradeResult(score=round(float(score), 3), comment=comment)

    def _compute_best_matches(
            self,
            ref_vectors: np.ndarray,
            user_vectors: np.ndarray
    ) -> Sequence[float]:
        """
        Вычисляет оптимальное сопоставление тезисов с предложениями студента.
        Использует венгерский алгоритм для максимизации суммарной схожести
        при ограничении "один тезис — одно предложение максимум"
        """
        if ref_vectors.shape[0] == 0:
            return []

        if user_vectors.shape[0] == 0:
            return [0.0] * ref_vectors.shape[0]

        similarity_matrix = np.dot(ref_vectors, user_vectors.T)
        row_indices, col_indices = linear_sum_assignment(-similarity_matrix)

        best_matches = {
            row: similarity_matrix[row, col]
            for row, col in zip(row_indices, col_indices)
        }

        return [
            float(best_matches.get(i, 0.0))
            for i in range(len(ref_vectors))
        ]

    def _generate_comment(
            self,
            reference_theses: Sequence[str],
            user_sentences: Sequence[str],
            ref_vectors: np.ndarray,
            user_vectors: np.ndarray,
            match_scores: Sequence[float],
    ) -> str:
        """
        Генерирует детальный комментарий о недостающих/неточных тезисах.
        Для каждого тезиса ниже порога находит наиболее близкое предложение
        студента и показывает степень близости
        """
        missed_items = []

        for thesis, score, ref_vec in zip(reference_theses, match_scores, ref_vectors):
            if score >= SIMILARITY_THRESHOLD:
                continue

            similarities = np.dot(ref_vec, user_vectors.T)
            best_idx = int(np.argmax(similarities))
            best_similarity = float(similarities[best_idx])
            best_sentence = user_sentences[best_idx] if user_sentences else "(нет предложений)"

            if best_similarity > SIMILARITY_CLOSE_THRESHOLD:
                missed_items.append(
                    f"• «{thesis}» → близко: «{best_sentence}» ({best_similarity:.2f})"
                )
            else:
                missed_items.append(f"• Не найдено: «{thesis}»")

        if not missed_items:
            return "Все тезисы найдены, но с небольшими отклонениями в формулировках."

        header = "Не полностью покрыты тезисы:\n"
        items = "\n".join(missed_items[:MAX_COMMENT_ITEMS])
        footer = (
            "\n… и ещё некоторые"
            if len(missed_items) > MAX_COMMENT_ITEMS
            else ""
        )

        return header + items + footer

    def _compute_vectors_batch(self, sentences: Sequence[str]) -> np.ndarray:
        """Вычисляет нормализованные эмбеддинги предложений для батча"""
        if not sentences:
            return np.zeros((0, self.vector_size), dtype=np.float32)

        filtered_sentences = []
        for sentence in sentences:
            tokens = self.tokenizer.tokenize(sentence)
            if len(tokens) >= MIN_TOKEN_COUNT:
                filtered_sentences.append(sentence)

        if not filtered_sentences:
            return np.zeros((len(sentences), self.vector_size), dtype=np.float32)

        inputs = self.tokenizer(
            filtered_sentences,
            return_tensors="np",
            padding=True,
            truncation=True,
            max_length=MAX_SEQUENCE_LENGTH,
        )

        outputs = self.session.run(
            None,
            {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64),
            },
        )
        last_hidden_state = outputs[0].astype(np.float32)

        embeddings = self._apply_mean_pooling(
            hidden_states=last_hidden_state,
            attention_mask=inputs["attention_mask"],
        )

        embeddings = self._normalize_vectors(embeddings)

        result = np.zeros((len(sentences), self.vector_size), dtype=np.float32)
        result[: len(filtered_sentences)] = embeddings

        return result

    @staticmethod
    def _apply_mean_pooling(
            hidden_states: np.ndarray,
            attention_mask: np.ndarray,
    ) -> np.ndarray:
        """Применяет mean pooling с учётом attention mask."""
        mask = attention_mask[..., None].astype(np.float32)
        masked_hidden = hidden_states * mask

        summed = masked_hidden.sum(axis=1)
        token_counts = mask.sum(axis=1)
        token_counts = np.clip(token_counts, 1e-9, None)

        return summed / token_counts

    @staticmethod
    def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
        """Применяет L2-нормализацию к векторам"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return vectors / norms

    @staticmethod
    def _split_sentences(text: str) -> Sequence[str]:
        """Разбивает текст на предложения и фильтрует слишком короткие"""
        normalized = text.replace("\n", " ").strip()
        sentences = [s.text.strip() for s in sentenize(normalized)]
        return [s for s in sentences if len(s) >= MIN_SENTENCE_LENGTH]
