import numpy as np
from razdel import sentenize
from scipy.optimize import linear_sum_assignment
from typing import Sequence, List, Dict

SIMILARITY_THRESHOLD: float = 0.7
SIMILARITY_CLOSE_THRESHOLD: float = 0.5
MAX_COMMENT_ITEMS: int = 5
MIN_SENTENCE_LENGTH: int = 10

from labstructanalyzer.schemas.answer import GradeResult
from labstructanalyzer.utils.embedder import TextEmbedder


class ThesisAnswerGrader:
    """Оценщик студенческих ответов на основе семантического сравнения тезисов с эталоном"""

    def __init__(self, embedder: TextEmbedder):
        self.embedder = embedder

    def is_processable(self, given: str, reference: str) -> bool:
        return True

    def grade(self, given: str, reference: str) -> GradeResult:
        """
        Оценивает ответ студента относительно эталона.
        Возвращает результат оценки с баллом [0.0, 1.0] и комментарием для преподавателя, если балл не полный.
        """
        given = given.strip()
        reference = reference.strip()

        user_sentences = self._split_sentences(given)
        reference_theses = self._split_sentences(reference)

        if not reference_theses:
            return GradeResult(score=0.0, comment="Эталон не содержит букв")

        if not user_sentences:
            return GradeResult(score=0.0, comment="Ответ пустой")

        ref_vectors = self.embedder.compute_embeddings(reference_theses)
        user_vectors = self.embedder.compute_embeddings(user_sentences)

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
    ) -> List[float]:
        """Вычисляет оптимальное сопоставление тезисов с предложениями студента"""
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

        return [float(best_matches.get(i, 0.0)) for i in range(len(ref_vectors))]

    def _generate_comment(
            self,
            reference_theses: Sequence[str],
            user_sentences: Sequence[str],
            ref_vectors: np.ndarray,
            user_vectors: np.ndarray,
            match_scores: Sequence[float],
    ) -> str | None:
        """Генерирует структурированный комментарий для преподавателя, разделяя пропущенные и слабо раскрытые тезисы"""
        missed_theses: List[Dict[str, str]] = []
        weakly_covered: List[Dict[str, str]] = []

        for thesis, score, ref_vec in zip(reference_theses, match_scores, ref_vectors):
            if score >= SIMILARITY_THRESHOLD:
                continue

            similarities = np.dot(ref_vec, user_vectors.T)
            best_idx = int(np.argmax(similarities))
            best_similarity = float(similarities[best_idx])
            best_sentence = user_sentences[best_idx] if user_sentences else "(нет предложений)"

            item_data = {
                "thesis": thesis,
                "student_version": best_sentence,
                "score": best_similarity
            }

            if best_similarity > SIMILARITY_CLOSE_THRESHOLD:
                weakly_covered.append(item_data)
            else:
                missed_theses.append(item_data)

        comment_parts = []

        if missed_theses:
            comment_parts.append("Не указаны:")
            for item in missed_theses[:MAX_COMMENT_ITEMS]:
                comment_parts.append(f"  • {item['thesis']}")

        if weakly_covered:
            comment_parts.append("\nУказаны частично:")
            for item in weakly_covered[:MAX_COMMENT_ITEMS]:
                comment_parts.append(
                    f"  • {item['thesis']} (сходство: {item['score']:.2f})"
                )
                comment_parts.append(f"    → Студент написал: «{item['student_version']}»")

        if not comment_parts:
            return None

        return "\n".join(comment_parts)

    @staticmethod
    def _split_sentences(text: str) -> Sequence[str]:
        """Разбивает текст на предложения и фильтрует слишком короткие."""
        normalized = text.replace("\n", " ").strip()
        sentences = [s.text.strip() for s in sentenize(normalized)]
        return [s for s in sentences if len(s) >= MIN_SENTENCE_LENGTH]
