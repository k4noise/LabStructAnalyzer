from dataclasses import asdict
from typing import Optional, Sequence

from labstructanalyzer.schemas.answer import AnswerResponse, GradeResult, PreGradedAnswerResponse
from labstructanalyzer.services.graders.thesis import ThesisAnswerGrader
from labstructanalyzer.services.graders.fixed import FixedAnswerGrader
from labstructanalyzer.services.graders.param import ParametrizedAnswerGrader
from labstructanalyzer.utils.embedder import TextEmbedder


class PreGraderService:
    """
    Сервис предварительной оценки ответов по эталонным ответам преподавателя
    """

    def __init__(self, answers: Sequence[AnswerResponse]) -> None:
        self._answers: Sequence[AnswerResponse] = answers
        self._strategies = [
            ParametrizedAnswerGrader({a.custom_id: a for a in answers}),
            FixedAnswerGrader(),
            ThesisAnswerGrader(TextEmbedder()),
        ]

    def grade(self, answer: AnswerResponse) -> PreGradedAnswerResponse | None:
        if not self._is_processable(answer):
            return None

        user_text = answer.data.get("data").get("text", "")
        best_result: Optional[GradeResult] = None

        for grader in self._strategies:
            if not grader.is_processable(user_text, answer.reference):
                continue

            current_result = grader.grade(user_text, answer.reference)
            if best_result is None or current_result.score > best_result.score:
                best_result = current_result

        if best_result:
            return PreGradedAnswerResponse.from_response(answer, asdict(best_result))

    def grade_many(self) -> Sequence[PreGradedAnswerResponse]:
        """
        Проводит предварительную оценку всех доступных непустых ответов
        при условии существования стратегии проверки

        Returns:
            Список оценённых объектов `Answer` для последующего сохранения в БД
        """
        return [self.grade(answer) for answer in self._answers]

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

        data = answer.data.get("data") or {}
        return bool(data.get("text") and answer.reference)
