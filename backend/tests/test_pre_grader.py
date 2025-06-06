import unittest
from unittest.mock import Mock, patch
from dataclasses import dataclass

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.models.dto.answer import FullAnswerData
from labstructanalyzer.models.answer_type import AnswerType


@dataclass
class GradeResult:
    score: float
    feedback: str


class TestPreGraderService(unittest.TestCase):
    def setUp(self):
        self.mock_fixed_grader = Mock()
        self.mock_param_grader = Mock()
        self.mock_arg_grader = Mock()

        self.patches = [
            patch('labstructanalyzer.services.pre_grader.FixedAnswerGrader',
                  return_value=self.mock_fixed_grader),
            patch('labstructanalyzer.services.pre_grader.ParametrizedAnswerGrader',
                  return_value=self.mock_param_grader),
            patch('labstructanalyzer.services.pre_grader.ArgumentAnswerGrader',
                  return_value=self.mock_arg_grader)
        ]

        for p in self.patches:
            p.start()

        from labstructanalyzer.services.pre_grader import PreGraderService
        self.PreGraderService = PreGraderService

        self.mock_answer = Mock(spec=Answer)
        self.mock_answer.data = {"text": "test answer"}

        self.mock_full_answer = Mock(spec=FullAnswerData)
        self.mock_full_answer.user_origin = self.mock_answer
        self.mock_full_answer.reference = "reference answer"
        self.mock_full_answer.custom_id = "test_id"
        self.mock_full_answer.type = AnswerType.simple

    def tearDown(self):
        for patch in self.patches:
            patch.stop()

    def test_init_creates_strategies(self):
        answers = [self.mock_full_answer]
        service = self.PreGraderService(answers)

        self.assertEqual(service._strategies[AnswerType.simple], self.mock_fixed_grader)
        self.assertEqual(service._strategies[AnswerType.param], self.mock_param_grader)
        self.assertEqual(service._strategies[AnswerType.arg], self.mock_arg_grader)

    def test_param_grader_gets_correct_param_map(self):
        """Проверяем, что ParametrizedAnswerGrader получает правильный param_map"""
        from labstructanalyzer.services.pre_grader import ParametrizedAnswerGrader

        answers = [self.mock_full_answer]
        _ = self.PreGraderService(answers)

        ParametrizedAnswerGrader.assert_called_once_with({self.mock_full_answer.custom_id: self.mock_full_answer})

    def test_grade_simple_answer(self):
        """Проверяем оценку простого ответа"""
        grade_result = GradeResult(score=1.0, feedback="Perfect")
        self.mock_fixed_grader.grade.return_value = grade_result

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.mock_fixed_grader.grade.assert_called_once_with("test answer", "reference answer")
        self.assertEqual(self.mock_answer.pre_grade, {"score": 1.0, "feedback": "Perfect"})
        self.assertEqual(result, [self.mock_answer])

    def test_grade_param_answer(self):
        """Проверяем оценку параметризованного ответа"""
        self.mock_full_answer.type = AnswerType.param
        grade_result = GradeResult(score=0.5, feedback="Partial")
        self.mock_param_grader.grade.return_value = grade_result

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.mock_param_grader.grade.assert_called_once_with("test answer", "reference answer")
        self.assertEqual(self.mock_answer.pre_grade, {"score": 0.5, "feedback": "Partial"})
        self.assertEqual(result, [self.mock_answer])

    def test_grade_with_unknown_type(self):
        """Проверяем обработку неизвестного типа ответа"""
        self.mock_full_answer.type = "unknown_type"

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.assertEqual(result, [])

    def test_grade_skips_empty_text(self):
        """Проверяем пропуск ответа с пустым текстом"""
        self.mock_answer.data = {"text": ""}

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.assertEqual(result, [])
        self.mock_fixed_grader.grade.assert_not_called()

    def test_grade_skips_empty_reference(self):
        """Проверяем пропуск ответа с пустым эталоном"""
        self.mock_full_answer.reference = ""

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.assertEqual(result, [])
        self.mock_fixed_grader.grade.assert_not_called()

    def test_grade_skips_none_data(self):
        """Проверяем пропуск ответа с None в data"""
        self.mock_answer.data = None

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.assertEqual(result, [])
        self.mock_fixed_grader.grade.assert_not_called()

    def test_grade_multiple_answers(self):
        """Проверяем обработку нескольких ответов"""
        answer1 = Mock(spec=FullAnswerData)
        answer1.type = AnswerType.arg
        answer1.user_origin = Mock(spec=Answer)
        answer1.user_origin.data = {"text": "answer1"}
        answer1.reference = "ref1"
        answer1.custom_id = "id1"

        answer2 = Mock(spec=FullAnswerData)
        answer2.type = AnswerType.simple
        answer2.user_origin = Mock(spec=Answer)
        answer2.user_origin.data = {"text": "answer2"}
        answer2.reference = "ref2"
        answer2.custom_id = "id2"

        grade_results = [
            GradeResult(score=0.7, feedback="Good"),
            GradeResult(score=0.9, feedback="Very good")
        ]
        self.mock_arg_grader.grade.return_value = grade_results[0]
        self.mock_fixed_grader.grade.return_value = grade_results[1]

        service = self.PreGraderService([answer1, answer2])
        result = service.grade()

        self.assertEqual(len(result), 2)
        self.mock_arg_grader.grade.assert_called_once_with("answer1", "ref1")
        self.mock_fixed_grader.grade.assert_called_once_with("answer2", "ref2")


if __name__ == '__main__':
    unittest.main()
