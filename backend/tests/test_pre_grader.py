import unittest
from unittest.mock import Mock, patch
from dataclasses import dataclass, asdict

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.schemas.answer import AnswerDto


@dataclass
class GradeResult:
    score: float
    feedback: str


class TestPreGraderService(unittest.TestCase):
    def setUp(self):
        self.mock_param_grader = Mock()
        self.mock_fixed_grader = Mock()
        self.mock_thesis_grader = Mock()

        self.patches = [
            patch('labstructanalyzer.services.pre_grader.ParametrizedAnswerGrader',
                  return_value=self.mock_param_grader),
            patch('labstructanalyzer.services.pre_grader.FixedAnswerGrader',
                  return_value=self.mock_fixed_grader),
            patch('labstructanalyzer.services.pre_grader.ThesisAnswerGrader',
                  return_value=self.mock_thesis_grader)
        ]

        for p in self.patches:
            p.start()

        from labstructanalyzer.services.pre_grader import PreGraderService
        self.PreGraderService = PreGraderService

        self.mock_data = Mock(spec=Answer)
        self.mock_data.data = {"text": "test answer"}

        self.mock_full_answer = Mock(spec=AnswerDto)
        self.mock_full_answer.data = self.mock_data
        self.mock_full_answer.reference = "reference answer"
        self.mock_full_answer.custom_id = "test_id"

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_init_creates_strategies(self):
        """Проверка инициализации списка грейдеров в правильном порядке"""
        answers = [self.mock_full_answer]
        service = self.PreGraderService(answers)

        self.assertEqual(service._strategies[0], self.mock_param_grader)
        self.assertEqual(service._strategies[1], self.mock_fixed_grader)
        self.assertEqual(service._strategies[2], self.mock_thesis_grader)

    def test_param_grader_gets_correct_param_map(self):
        """Проверка: ParametrizedAnswerGrader получает корректный param_map"""
        from labstructanalyzer.services.pre_grader import ParametrizedAnswerGrader

        answers = [self.mock_full_answer]
        _ = self.PreGraderService(answers)

        ParametrizedAnswerGrader.assert_called_once_with({
            self.mock_full_answer.custom_id: self.mock_full_answer
        })

    def test_grade_chooses_best_grader(self):
        """Проверка: выбирается грейдер с наивысшим score"""
        self.mock_param_grader.is_processable.return_value = False
        self.mock_fixed_grader.is_processable.return_value = True
        self.mock_thesis_grader.is_processable.return_value = True

        self.mock_fixed_grader.grade.return_value = GradeResult(1.0, "Perfect")
        self.mock_thesis_grader.grade.return_value = GradeResult(0.8, "Good")

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.mock_fixed_grader.grade.assert_called_once_with(
            "test answer", "reference answer"
        )
        self.assertEqual(self.mock_data.pre_grade, {
            "score": 1.0,
            "feedback": "Perfect"
        })
        self.assertEqual(result, [self.mock_data])

    def test_grade_skips_unprocessable_answers(self):
        """Проверка: пропускаются ответы, которые ни один грейдер не может обработать"""
        self.mock_param_grader.is_processable.return_value = False
        self.mock_fixed_grader.is_processable.return_value = False
        self.mock_thesis_grader.is_processable.return_value = False

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.mock_param_grader.grade.assert_not_called()
        self.mock_fixed_grader.grade.assert_not_called()
        self.mock_thesis_grader.grade.assert_not_called()
        self.assertEqual(result, [])

    def test_grade_skips_empty_text(self):
        """Проверка: пропуск ответов с пустым текстом"""
        self.mock_data.data = {"text": ""}

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.mock_param_grader.grade.assert_not_called()
        self.assertEqual(result, [])

    def test_grade_skips_missing_reference(self):
        """Проверка: пропуск ответов без эталона"""
        self.mock_full_answer.reference = None

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.mock_fixed_grader.grade.assert_not_called()
        self.assertEqual(result, [])

    def test_grade_multiple_answers(self):
        """Проверяем обработку нескольких ответов разными грейдерами"""
        data1 = Mock(spec=Answer)
        data1.data = {"text": "answer1"}

        full_answer1 = Mock(spec=AnswerDto)
        full_answer1.data = data1
        full_answer1.reference = "ref1"
        full_answer1.custom_id = "id1"

        data2 = Mock(spec=Answer)
        data2.data = {"text": "answer2"}

        full_answer2 = Mock(spec=AnswerDto)
        full_answer2.data = data2
        full_answer2.reference = "ref2"
        full_answer2.custom_id = "id2"

        grade_result1 = GradeResult(score=0.7, feedback="Good")
        grade_result2 = GradeResult(score=0.9, feedback="Very good")

        self.mock_thesis_grader.is_processable.side_effect = [True, False]
        self.mock_fixed_grader.is_processable.side_effect = [False, True]
        self.mock_param_grader.is_processable.return_value = False

        self.mock_thesis_grader.grade.return_value = grade_result1
        self.mock_fixed_grader.grade.return_value = grade_result2

        service = self.PreGraderService([full_answer1, full_answer2])
        result = service.grade()

        self.assertEqual(len(result), 2)

        self.mock_thesis_grader.grade.assert_called_once_with("answer1", "ref1")
        self.mock_fixed_grader.grade.assert_called_once_with("answer2", "ref2")

        self.assertEqual(data1.pre_grade, asdict(grade_result1))
        self.assertEqual(data2.pre_grade, asdict(grade_result2))

    def test_grade_with_none_data(self):
        """Проверка: пропуск ответов с None в data"""
        self.mock_data.data = None

        service = self.PreGraderService([self.mock_full_answer])
        result = service.grade()

        self.mock_param_grader.grade.assert_not_called()
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
