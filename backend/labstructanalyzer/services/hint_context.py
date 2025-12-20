import uuid
from datetime import timedelta
from typing import Sequence, Tuple, Dict, List

import numpy as np

from labstructanalyzer.exceptions.access_denied import NotOwnerAccessDeniedException
from labstructanalyzer.models.template_element import TemplateElement
from labstructanalyzer.models.user_model import User
from labstructanalyzer.schemas.hint import NewHintRequest, HintGenerationRequest
from labstructanalyzer.schemas.template import FullWorkResponse
from labstructanalyzer.schemas.template_element import TemplateElementProperties
from labstructanalyzer.services.pre_grader import PreGraderService
from labstructanalyzer.utils.embedder import TextEmbedder
from labstructanalyzer.utils.ttl_cache import RedisCache


class HintContextService:
    def __init__(self, embedder: TextEmbedder):
        self.embedder = embedder

    @staticmethod
    def cache(report: FullWorkResponse, cache: RedisCache):
        """Кэширует данные элементов шаблона и динамический контекст отчета"""
        if not report.template.elements:
            return

        elements_data = {
            f"template_element_{element.id}": element.properties
            for element in report.template.elements
        }
        cache.set_many_if_not_present(elements_data, timedelta(hours=3))

        report_data = {
            "status": report.status.value,
            "author_id": report.author_id
        }

        cache.set(f"live_report_{report.id}", report_data, ttl=timedelta(hours=1))

    @staticmethod
    def get_from_cache(hint_request: NewHintRequest, user: User, report_id: uuid.UUID,
                       cache: RedisCache) -> HintGenerationRequest | None:
        """Собирает контекст из кэша для отправки на генерацию подсказки"""

        report_data = cache.get(f"live_report_{report_id}")
        if report_data and report_data['author_id'] != user.sub:
            raise NotOwnerAccessDeniedException()

        answer_element = cache.get(f"template_element_{hint_request.current.element_id}")
        if not answer_element:
            return None

        hint_request.current.reference = answer_element.get("refAnswer")
        pre_graded = PreGraderService(hint_request.params).grade(hint_request.current)
        question_element = cache.get(f"template_element_{hint_request.question_id}")

        theory_data = []

        similar_theory_ids = []
        if answer_element and getattr(answer_element, 'properties', None):
            similar_theory_ids = answer_element.properties.get("similar_theory", [])

        for theory_id in similar_theory_ids:
            theory_element = cache.get(f"template_element_{theory_id}")
            if theory_element:
                theory_data.append(theory_element.properties.get("data"))

        return HintGenerationRequest(
            answer=hint_request.current.data.get("text"),
            question=question_element.get("data", "") if question_element else "",
            theory=theory_data,
            error_explanation=pre_graded.pre_grade.get("comment"),
            pre_score=pre_graded.pre_grade.get("score")
        )

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
                properties={"similar_theory": top_similar_ids}
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

        texts = [element.properties.get("data") for element in elements]
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
        return [str(item[0]) for item in sorted_scores[:top_k]]
