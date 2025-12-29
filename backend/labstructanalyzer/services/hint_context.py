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

        elements: Sequence[TemplateElement] = report.template.elements
        children = HintContextService._build_children_index(elements)

        elements_data: Dict[str, dict] = {}
        for element in elements:
            props = dict(element.properties or {})

            if element.type == "question":
                q_text = HintContextService._get_question_text(element, children)
                if isinstance(q_text, str):
                    props["data"] = q_text

            elements_data[f"template_element_{element.id}"] = props

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

        # в кэше лежат только properties элемента-ответа
        answer_element: dict | None = cache.get(f"template_element_{hint_request.current.element_id}")
        if not answer_element:
            return None

        hint_request.current.reference = answer_element.get("refAnswer")
        pre_graded = PreGraderService(hint_request.params).grade(hint_request.current)

        question_text: str | None = answer_element.get("question_text")
        similar_theory_ids: List[str] = answer_element.get("similar_theory", []) or []

        question_element: dict | None = None

        if not question_text or not similar_theory_ids:
            question_id = getattr(hint_request, "question_id", None) or answer_element.get("question_id")
            if question_id:
                question_element = cache.get(f"template_element_{question_id}")
                if question_element:
                    if not question_text:
                        qt = question_element.get("data")
                        if isinstance(qt, str):
                            question_text = qt
                    if not similar_theory_ids:
                        similar_theory_ids = question_element.get("similar_theory", []) or []

        theory_data: List[str] = []
        for theory_id in similar_theory_ids:
            theory_element: dict | None = cache.get(f"template_element_{theory_id}")
            if theory_element:
                text = theory_element.get("data")
                if isinstance(text, str):
                    theory_data.append(text)

        return HintGenerationRequest(
            answer=hint_request.current.data.get("text"),
            question=question_text or "",
            theory=theory_data,
            error_explanation=pre_graded.pre_grade.get("comment"),
            pre_score=pre_graded.pre_grade.get("score")
        )

    def analyze(self, template_elements: Sequence[TemplateElement]) -> Sequence[TemplateElementProperties]:
        """Для каждого вопроса находит 3 наиболее похожих элемента теории"""
        questions, theory = self._separate_questions_and_theory(template_elements)

        if not questions or not theory:
            return []

        children = self._build_children_index(template_elements)

        q_ids: List[uuid.UUID] = []
        q_texts: List[str] = []
        question_texts: Dict[uuid.UUID, str] = {}

        for question in questions:
            q_text = self._get_question_text(question, children)
            if isinstance(q_text, str) and q_text.strip():
                q_ids.append(question.id)
                q_texts.append(q_text)
                question_texts[question.id] = q_text

        if not q_texts:
            return []

        q_embeddings = self.embedder.compute_embeddings(q_texts)
        question_embeddings_map: Dict[uuid.UUID, np.ndarray] = {
            qid: vec for qid, vec in zip(q_ids, q_embeddings)
        }

        theory_embeddings_map = self._create_embedding_map(theory)

        results: List[TemplateElementProperties] = []
        for question in questions:
            question_vector = question_embeddings_map.get(question.id)
            if question_vector is None:
                continue

            top_similar_ids = self._find_top_similar_ids(
                question_vector=question_vector,
                candidates_map=theory_embeddings_map,
                top_k=3
            )

            results.append(TemplateElementProperties(
                id=question.id,
                properties={**question.properties, "similar_theory": top_similar_ids}
            ))

            q_text = question_texts.get(question.id)
            for child in children.get(question.id, []):
                if child.type == "answer":
                    props = {
                        **(child.properties or {}),
                        "similar_theory": top_similar_ids,
                        "question_id": str(question.id),
                    }
                    if q_text:
                        props.setdefault("question_text", q_text)

                    results.append(TemplateElementProperties(
                        id=child.id,
                        properties=props
                    ))

        return results

    def _separate_questions_and_theory(self, template_elements: Sequence[TemplateElement]) -> Tuple[
        List[TemplateElement], List[TemplateElement]]:
        """Разделяет входящие элементы на вопросы и теорию"""
        questions, theory = [], []
        for element in template_elements:
            if element.type == 'question':
                questions.append(element)
            elif element.type == 'text':
                if element.parent_element_id is None:
                    theory.append(element)
        return questions, theory

    def _create_embedding_map(self, elements: Sequence[TemplateElement]) -> Dict[uuid.UUID, np.ndarray]:
        """Создает словарь {id элемента: эмбеддинг} для списка элементов"""
        if not elements:
            return {}

        ids: List[uuid.UUID] = []
        texts: List[str] = []

        for element in elements:
            text = (element.properties or {}).get("data")
            if isinstance(text, str) and text.strip():
                ids.append(element.id)
                texts.append(text)

        if not texts:
            return {}

        embeddings = self.embedder.compute_embeddings(texts)
        return {el_id: vec for el_id, vec in zip(ids, embeddings)}

    def _find_top_similar_ids(self, question_vector: np.ndarray, candidates_map: Dict[uuid.UUID, np.ndarray],
                              top_k: int) -> List[str]:
        """Находит top_k самых похожих кандидатов по косинусному сходству"""
        scores = []
        for candidate_id, candidate_vector in candidates_map.items():
            similarity = self.embedder.cosine_similarity(question_vector, candidate_vector)
            scores.append((candidate_id, similarity))

        sorted_scores = sorted(scores, key=lambda item: item[1], reverse=True)
        return [str(item[0]) for item in sorted_scores[:top_k]]

    @staticmethod
    def _build_children_index(elements: Sequence[TemplateElement]) -> Dict[uuid.UUID, List[TemplateElement]]:
        """Индекс детей по parent_element_id"""
        children: Dict[uuid.UUID, List[TemplateElement]] = {}
        print(elements)
        for el in elements:
            if el.parent_id:
                children.setdefault(el.parent_id, []).append(el)

        return children

    @staticmethod
    def _get_question_text(question: TemplateElement,
                           children_index: Dict[uuid.UUID, List[TemplateElement]]) -> str | None:
        direct = (question.properties or {}).get("data")
        if isinstance(direct, str) and direct.strip():
            return direct

        childs = children_index.get(question.id, [])
        for child in childs:
            if child.type == "text":
                text = (child.properties or {}).get("data")
                if isinstance(text, str) and text.strip():
                    return text

        return None
