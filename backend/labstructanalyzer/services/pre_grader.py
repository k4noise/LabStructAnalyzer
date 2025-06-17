import logging
from dataclasses import asdict
from typing import List, Optional

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.models.dto.answer import FullAnswerData, GradeResult
from labstructanalyzer.services.graders.thesis import ThesisAnswerGrader
from labstructanalyzer.services.graders.fixed import FixedAnswerGrader
from labstructanalyzer.services.graders.param import ParametrizedAnswerGrader


class PreGraderService:
    """
    Сервис предварительной оценки ответов по эталонным ответам преподавателя
    """

    def __init__(self, answers: List[FullAnswerData]) -> None:
        self._answers: List[FullAnswerData] = answers
        self._strategies = [
            ParametrizedAnswerGrader({a.custom_id: a for a in answers}),
            FixedAnswerGrader(),
            ThesisAnswerGrader(),
        ]

    def grade(self) -> List[Answer]:
        """
        Проводит предварительную оценку всех доступных непустых ответов
        при условии существования стратегии проверки

        Returns:
            Список оценённых объектов `Answer` для последующего сохранения в БД
        """
        graded: List[Answer] = []

        for answer in self._answers:
            if not self._is_processable(answer):
                continue

            user_text = answer.user_origin.data.get("text", "")
            best_result: Optional[GradeResult] = None

            for grader in self._strategies:
                if not grader.is_processable(user_text, answer.reference):
                    continue

                current_result = grader.grade(user_text, answer.reference)
                if best_result is None or current_result.score > best_result.score:
                    best_result = current_result

            if best_result:
                answer.user_origin.pre_grade = asdict(best_result)
                graded.append(answer.user_origin)

        return graded

    @staticmethod
    def _is_processable(answer: FullAnswerData) -> bool:
        """
        Проверяет, готов ли ответ к оценке:
        - Существует user_origin
        - В ответе есть текст (user_origin.data["text"])
        - Есть эталон (answer.reference)

        Args:
            answer: Объект `FullAnswerData`, содержащий данные ответа

        Returns:
            True, если ответ можно обработать, иначе False
        """
        if not answer.user_origin:
            return False

        data = answer.user_origin.data or {}
        return bool(data.get("text") and answer.reference)
