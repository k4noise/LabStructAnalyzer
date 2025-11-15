import uuid
from typing import Sequence, Tuple, Dict, List

import numpy as np

from labstructanalyzer.models.template_element import TemplateElement
from labstructanalyzer.schemas.template_element import TemplateElementProperties
from labstructanalyzer.utils.embedder import TextEmbedder


class TemplateMatcher:
    def __init__(self, embedder: TextEmbedder):
        self.embedder = embedder

    def analyze(self, template_elements: Sequence[TemplateElement]) -> Sequence[TemplateElementProperties]:
        """Для каждого вопроса находит 3 наиболее похожих элемента теории"""
        questions, theory = self._separate_questions_and_theory(template_elements)

        if not questions or not theory:
            return []

        question_embeddings_map = self._create_embedding_map(questions)
        theory_embeddings_map = self._create_embedding_map(theory)

        results = []
        for question in questions:
            question_vector = question_embeddings_map[question.id]

            top_similar_ids = self._find_top_similar_ids(
                question_vector=question_vector,
                candidates_map=theory_embeddings_map,
                top_k=3
            )

            results.append(TemplateElementProperties(
                id=question.id,
                properties={"similar": top_similar_ids}
            ))

        return results

    def _separate_questions_and_theory(self, template_elements: Sequence[TemplateElement]) -> Tuple[
        List[TemplateElement], List[TemplateElement]]:
        """Разделяет входящие элементы на вопросы и теорию"""
        questions, theory = [], []
        for element in template_elements:
            if element.type == 'text':
                theory.append(element)
            elif element.type == 'question':
                questions.append(element)
        return questions, theory

    def _create_embedding_map(self, elements: Sequence[TemplateElement]) -> Dict[uuid.UUID, np.ndarray]:
        """Создает словарь {id элемента: эмбеддинг} для списка элементов"""
        if not elements:
            return {}

        texts = [el.data for el in elements]
        embeddings = self.embedder.compute_embeddings(texts)
        return {el.id: vec for el, vec in zip(elements, embeddings)}

    def _find_top_similar_ids(self, question_vector: np.ndarray, candidates_map: Dict[uuid.UUID, np.ndarray],
                              top_k: int) -> List[uuid.UUID]:
        """Находит top_k самых похожих кандидатов по косинусному сходству"""
        scores = []
        for candidate_id, candidate_vector in candidates_map.items():
            similarity = self.embedder.cosine_similarity(question_vector, candidate_vector)
            scores.append((candidate_id, similarity))

        sorted_scores = sorted(scores, key=lambda item: item[1], reverse=True)
        return [item[0] for item in sorted_scores[:top_k]]
