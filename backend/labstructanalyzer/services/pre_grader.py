from dataclasses import asdict
from typing import Optional, Sequence

from labstructanalyzer.schemas.answer import AnswerResponse, GradeResult, PreGradedAnswerResponse
from labstructanalyzer.services.graders.thesis import ThesisAnswerGrader
from labstructanalyzer.services.graders.fixed import FixedAnswerGrader
from labstructanalyzer.services.graders.param import ParametrizedAnswerGrader


class PreGraderService:
    """
    Сервис предварительной оценки ответов по эталонным ответам преподавателя
    """

    def __init__(self, answers: Sequence[AnswerResponse]) -> None:
        self._answers: Sequence[AnswerResponse] = answers
        self._strategies = [
            ParametrizedAnswerGrader({a.custom_id: a for a in answers}),
            FixedAnswerGrader(),
            ThesisAnswerGrader(),
        ]

    def grade(self) -> Sequence[PreGradedAnswerResponse]:
        """
        Проводит предварительную оценку всех доступных непустых ответов
        при условии существования стратегии проверки

        Returns:
            Список оценённых объектов `Answer` для последующего сохранения в БД
        """
        graded: list[PreGradedAnswerResponse] = []

        for answer in self._answers:
            if not self._is_processable(answer):
                continue

            user_text = answer.data.get("data").get("text", "")
            best_result: Optional[GradeResult] = None

            for grader in self._strategies:
                if not grader.is_processable(user_text, answer.reference):
                    continue

                current_result = grader.grade(user_text, answer.reference)
                if best_result is None or current_result.score > best_result.score:
                    best_result = current_result

            if best_result:
                answer.data.pre_grade = asdict(best_result)
                graded.append(answer.data)

        return graded

    @staticmethod
    def _is_processable(answer: AnswerResponse) -> bool:
        """
        Проверяет, готов ли ответ к оценке:
        - Существует data
        - В ответе есть текст (data.data["text"])
        - Есть эталон (answer.reference)

        Args:
            answer: Объект `FullAnswerData`, содержащий данные ответа

        Returns:
            True, если ответ можно обработать, иначе False
        """
        if not answer.data:
            return False

        data = answer.data.data or {}
        return bool(data.get("text") and answer.reference)
