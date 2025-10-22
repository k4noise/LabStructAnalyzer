import unittest

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.schemas.answer import AnswerResponse
from labstructanalyzer.services.graders.param import ParametrizedAnswerGrader


class TestParametrizedAnswerGrader(unittest.TestCase):
    """Тесты для ParametrizedAnswerGrader: параметры, диапазоны, подстановки."""

    @classmethod
    def setUpClass(cls):
        cls.empty_grader = ParametrizedAnswerGrader({})

    def test_empty_reference(self):
        """Пустой эталон → ответ всегда засчитывается"""
        result = self.empty_grader.grade("любой текст", "")
        self.assertEqual(result.score, 1)
        self.assertEqual(result.comment, "Эталон пуст")

    def test_exact_match(self):
        """Простое совпадение без параметров и диапазонов"""
        cases = [
            {
                "name": "Exact",
                "given": "Простой Ответ",
                "reference": "простой ответ",
                "score": 1
            },
            {
                "name": "Spaces",
                "given": "  текст  ",
                "reference": "текст",
                "score": 1
            },
            {
                "name": "Fail",
                "given": "другой",
                "reference": "ответ",
                "score": 0
            },
        ]
        for case in cases:
            with self.subTest(case=case["name"]):
                result = self.empty_grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["score"])

    def test_param_substitution(self):
        """Параметр {city} подставляется и используется в сравнении"""
        city = AnswerResponse(
            data=Answer(
                data={"text": "Москва"},
                pre_grade={"score": 1}
            )
        )
        grader = ParametrizedAnswerGrader({"city": city})

        cases = [
            {
                "name": "in middle",
                "given": "столица Москва",
                "reference": "столица {city}",
                "score": 1
            },
            {
                "name": "only param",
                "given": "МОСКВА",
                "reference": "{city}",
                "score": 1
            },
            {
                "name": "missing",
                "given": "Москва есть",
                "reference": "{city} город",
                "score": 0
            },
        ]
        for case in cases:
            with self.subTest(case=case["name"]):
                result = grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["score"])

    def test_param_with_pregrade_zero(self):
        """Если параметр имеет pre_grade=0 — всегда ошибка"""
        param = AnswerResponse(
            data=Answer(
                data={"text": "Питер"},
                pre_grade={"score": 0}
            )
        )
        grader = ParametrizedAnswerGrader({"city": param})

        result = grader.grade("столица Питер", "столица {city}")
        self.assertEqual(result.score, 0)
        self.assertEqual(result.wrong_params, ["city"])
        self.assertEqual(result.comment, "Параметр 'city' предварительно неверен (score=0)")

    def test_unknown_param_is_literal(self):
        """{unknown_param} → остаётся литералом и ищется как обычный текст"""
        ok = self.empty_grader.grade("текст {foo}", "текст {foo}")
        self.assertEqual(ok.score, 1)

        fail = self.empty_grader.grade("текст foo", "текст {foo}")
        self.assertEqual(fail.score, 0)
        self.assertIsNone(fail.wrong_params)
        self.assertEqual(fail.comment, "Не найден обязательный фрагмент: 'текст {foo}'")

    def test_integer_range_check(self):
        """[1-5] содержит целые и float (`3.5`)"""
        cases = [
            {
                "name": "lower",
                "given": "число 1",
                "reference": "число [1-5]",
                "score": 1
            },
            {
                "name": "upper",
                "given": "число 5",
                "reference": "число [1-5]",
                "score": 1
            },
            {
                "name": "below",
                "given": "число 0",
                "reference": "число [1-5]",
                "score": 0
            },
            {
                "name": "above",
                "given": "число 6",
                "reference": "число [1-5]",
                "score": 0
            },
            {
                "name": "mid float",
                "given": "число 3.5",
                "reference": "число [1-5]",
                "score": 1
            },
        ]
        for case in cases:
            with self.subTest(case=case["name"]):
                result = self.empty_grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["score"])

    def test_float_range_check(self):
        """[1.0–2.0] допускает как float, так и int"""
        cases = [
            {
                "name": "float",
                "given": "v 1.5",
                "reference": "v [1.0-2.0]",
                "score": 1
            },
            {
                "name": "int",
                "given": "v 1",
                "reference": "v [1.0-2.0]",
                "score": 1
            },
            {
                "name": "below",
                "given": "v 0.9",
                "reference": "v [1.0-2.0]",
                "score": 0
            },
        ]
        for case in cases:
            with self.subTest(case=case["name"]):
                result = self.empty_grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["score"])

    def test_alternative_set_check(self):
        """[2|4|6] принимает только указанные варианты"""
        for val, expected in [("2", 1), ("4", 1), ("6", 1), ("3", 0)]:
            with self.subTest(f"alt={val}"):
                result = self.empty_grader.grade(f"num {val}", "num [2|4|6]")
                self.assertEqual(result.score, expected)

    def test_mixed_alternatives_and_ranges(self):
        """Смешанные альтернативы и диапазоны: [5|1-3|15]"""
        cases = [
            ("num 5", 1),
            ("num 2", 1),
            ("num 3", 1),
            ("num 15", 1),
            ("num 4", 0),
        ]
        for given, expected in cases:
            with self.subTest(given=given):
                result = self.empty_grader.grade(given, "num [5|1-3|15]")
                self.assertEqual(result.score, expected)

    def test_multiline_reference(self):
        """Многострочный эталон: все строки должны совпасть"""
        ref = "first.\nsecond [1-2].\nthird foo"
        ok = self.empty_grader.grade("first. second 2. third foo", ref)
        fail = self.empty_grader.grade("first. second 3. third foo", ref)

        self.assertEqual(ok.score, 1)
        self.assertEqual(fail.score, 0)
        self.assertEqual(
            fail.comment,
            "В тезисе 'second [1-2].' значение '3' не попадает в диапазон [1–2]"
        )

    def test_param_inside_range(self):
        """Параметр в скобках: [1-{max}] заменяется и парсится корректно"""
        param = AnswerResponse(
            data=Answer(
                data={"text": "5"},
                pre_grade={"score": 1}
            )
        )
        grader = ParametrizedAnswerGrader({"max": param})
        result = grader.grade("val 3", "val [1-{max}]")
        self.assertEqual(result.score, 1)

    def test_repeated_param_usage(self):
        """Один и тот же параметр подставляется несколько раз"""
        param = AnswerResponse(
            data=Answer(
                data={"text": "rep"},
                pre_grade={"score": 1}
            )
        )
        grader = ParametrizedAnswerGrader({"x": param})
        result = grader.grade("rep and rep and rep", "{x} and {x} and {x}")
        self.assertEqual(result.score, 1)

    def test_invalid_range_spec_is_literal(self):
        """Некорректное содержимое в скобках (напр. [что-то]) → ищется как literal"""
        result = self.empty_grader.grade("foo", "val [что-то]")
        self.assertEqual(result.score, 0)
        self.assertEqual(result.comment, "Не найдено соответствие для тезиса: 'val [что-то]'")

    def test_text_normalization(self):
        """Проверка, что пробелы и регистр игнорируются."""
        result = self.empty_grader.grade("  TeXt   123 ", "text 123")
        self.assertEqual(result.score, 1)

    def test_complex_reference_with_param_and_range(self):
        """Сложный тезис: параметр + диапазон вперемешку"""
        param = AnswerResponse(
            data=Answer(
                data={"text": "London"},
                pre_grade={"score": 1}
            )
        )
        grader = ParametrizedAnswerGrader({"city": param})

        given = "This is text with London and code 3 inside"
        ref = "This is text with {city} and code [1-5] inside"
        result = grader.grade(given, ref)
        self.assertEqual(result.score, 1)

    def test_literal_square_brackets_double_syntax(self):
        """
        [[text]] → интерпретируется как литерал с квадратными скобками.
        Проверяется совпадение, несовпадение, множественные случаи и сочетания с диапазонами.
        """
        grader = self.empty_grader

        cases = [
            {
                "name": "single literal match",
                "given": "Ответ: [42]",
                "reference": "Ответ: [[42]]",
                "score": 1
            },
            {
                "name": "single literal mismatch (no brackets)",
                "given": "Ответ: 42",
                "reference": "Ответ: [[42]]",
                "score": 0,
                "comment": "Не найден обязательный фрагмент: 'Ответ: [42]'"
            },
            {
                "name": "multiple literals in one line",
                "given": "Значения: [A], [B]",
                "reference": "Значения: [[A]], [[B]]",
                "score": 1
            },
            {
                "name": "literal and range combination: success",
                "given": "значение [42] и число 3",
                "reference": "значение [[42]] и число [1-5]",
                "score": 1
            },
            {
                "name": "literal and range combination: fail on range",
                "given": "значение [42] и число 6",
                "reference": "значение [[42]] и число [1-5]",
                "score": 0,
                "comment": "В тезисе 'значение [42] и число [1-5]' значение '6' не попадает в диапазон [1–5]"
            },
            {
                "name": "multiline with literal",
                "given": "строка 1 строка [42] строка 3",
                "reference": "строка 1\nстрока [[42]]\nстрока 3",
                "score": 1
            },
            {
                "name": "multiline with missing literal",
                "given": "строка 1 строка 42 строка 3",
                "reference": "строка 1\nстрока [[42]]\nстрока 3",
                "score": 0,
                "comment": "Не найден обязательный фрагмент: 'строка [42]'"
            },
            {
                "name": "content with | alt syntax inside [[...]]",
                "given": "файл [v3|v4]",
                "reference": "файл [[v3|v4]]",
                "score": 1
            },
            {
                "name": "content with | in text, not matching",
                "given": "файл v3",
                "reference": "файл [[v3|v4]]",
                "score": 0
            },
            {
                "name": "literal at end of line",
                "given": "скобка [x] здесь",
                "reference": "скобка [[x]] здесь",
                "score": 1
            },
        ]

        for case in cases:
            with self.subTest(case=case["name"]):
                result = grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["score"])
                if "comment" in case and case["score"] == 0:
                    self.assertEqual(result.comment, case["comment"])


if __name__ == "__main__":
    unittest.main()
