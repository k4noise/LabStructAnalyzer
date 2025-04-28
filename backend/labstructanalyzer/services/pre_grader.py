from dataclasses import asdict
from labstructanalyzer.models.answer import Answer
from labstructanalyzer.models.dto.answer import FullAnswerData
from labstructanalyzer.models.answer_type import AnswerType
from labstructanalyzer.services.graders.fixed import FixedAnswerGrader
from labstructanalyzer.services.graders.param import ParametrizedAnswerGrader


class PreGraderService:
    """Сервис предварительной оценки ответов по эталонным ответам преподавателя"""

    def __init__(self, answers: list[FullAnswerData]):
        parameters = {answer.custom_id: answer for answer in answers}

        self.answers = answers
        self._strategies = {
            AnswerType.simple.name: FixedAnswerGrader(),
            AnswerType.param.name: ParametrizedAnswerGrader(parameters)
        }

    def grade(self) -> list[Answer]:
        graded_answers = []
        for answer in self.answers:
            answer_text = answer.user_origin.data.get("text") if answer.user_origin.data else None

            if not answer_text or not answer.reference:
                continue

            strategy = self._strategies.get(answer.type.name)
            if not strategy:
                continue

            grade_result = strategy.grade(answer_text, answer.reference)
            answer.user_origin.pre_grade = asdict(grade_result)
            graded_answers.append(answer.user_origin)
        return graded_answers
