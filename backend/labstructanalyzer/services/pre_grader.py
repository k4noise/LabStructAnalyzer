from dataclasses import asdict

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.models.dto.answer import FullAnswerData
from labstructanalyzer.models.answer_type import AnswerType
from labstructanalyzer.services.graders.complex import ArgumentAnswerGrader
from labstructanalyzer.services.graders.fixed import FixedAnswerGrader
from labstructanalyzer.services.graders.param import ParametrizedAnswerGrader


class PreGraderService:
    """Сервис предварительной оценки ответов по эталонным ответам преподавателя"""

    def __init__(self, answers: list[FullAnswerData]) -> None:
        """Инициализирует сервис PreGraderService

        Args:
            answers: Список подготовленных к оценке данных ответов
                     с эталонными значениями преподавателя.
        """
        param_map = {a.custom_id: a for a in answers}

        self._answers: list[FullAnswerData] = answers
        self._strategies = {
            AnswerType.simple: FixedAnswerGrader(),
            AnswerType.param: ParametrizedAnswerGrader(param_map),
            AnswerType.arg: ArgumentAnswerGrader(),
        }

    def grade(self) -> list[Answer]:
        """Проводит предварительную оценку всех доступных непустых ответов
        при условии существования стратегии проверки

        Returns:
            Список оценённых объектов `Answer` для их последующего сохранения в БД
        """
        graded: list[Answer] = []

        for answer in self._answers:
            if not self._is_processable(answer):
                continue

            grader = self._strategies.get(answer.type)
            if not grader:
                continue

            user_text = answer.user_origin.data["text"]
            result = grader.grade(user_text, answer.reference)

            answer.user_origin.pre_grade = asdict(result)
            graded.append(answer.user_origin)

        return graded

    @staticmethod
    def _is_processable(answer: FullAnswerData) -> bool:
        """Проверяет, можно ли обработать переданный ответ

        Args:
            answer: Объект `FullAnswerData`, содержащий данные ответа

        Returns:
            Возможность обработки ответа - наличие ответа студента и эталонного тезиса
        """
        data = answer.user_origin.data or {}
        return bool(data.get("text") and answer.reference)
