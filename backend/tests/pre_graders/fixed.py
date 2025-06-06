import unittest

from labstructanalyzer.services.graders.fixed import FixedAnswerGrader


class FixedAnswerGraderTests(unittest.TestCase):
    """Тестирование работы всех этапов проверки ответов фиксированного типа"""

    @classmethod
    def setUpClass(cls):
        cls.grader = FixedAnswerGrader()

    def test_digits_mismatch(self):
        """Тестирование несовпадения цифр"""
        test_cases = [
            {
                "case_name": "One wrong with word",
                "given": "ответ 456",
                "reference": "ответ 123",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: '456', из эталона: '123'"
            },
            {
                "case_name": "One right, one wrong",
                "given": "123 456",
                "reference": "123 789",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: '123; 456', из эталона: '123; 789'"
            },
            {
                "case_name": "No digit, must present",
                "given": "ответ",
                "reference": "ответ 123",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: не найдены, из эталона: '123'"
            },
            {
                "case_name": "Different order",
                "given": "231",
                "reference": "123",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: '231', из эталона: '123'"
            },
            {
                "case_name": "Negative and positive",
                "given": "-5",
                "reference": "5",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: '-5', из эталона: '5'"
            },
            {
                "case_name": "Start in zero",
                "given": "011",
                "reference": "11",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: '011', из эталона: '11'"
            },
            {
                "case_name": "Zero different counts",
                "given": "00000",
                "reference": "000",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: '00000', из эталона: '000'"
            },
            {
                "case_name": "With delimiter and thousands",
                "given": "1,000.12",
                "reference": "1000.12",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: '1; 000; 12', из эталона: '1000; 12'"
            },
            {
                "case_name": "Different nums count",
                "given": "1 2",
                "reference": "1 2 16",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: '1; 2', из эталона: '1; 2; 16'"
            },
            {
                "case_name": "Different nums split",
                "given": "1.2.16",
                "reference": "12.16",
                "expected_score": 0,
                "expected_comment": "Цифры не совпадают, извлечено из ответа: '1; 2; 16', из эталона: '12; 16'"
            }
        ]
        for case in test_cases:
            with self.subTest(case=case["case_name"]):
                result = self.grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["expected_score"])
                self.assertEqual(result.comment, case["expected_comment"])

    def test_exact_match(self):
        """Тестирование точного совпадения"""
        test_cases = [
            {
                "case_name": "Only words",
                "given": "точный ответ",
                "reference": "точный ответ",
                "expected_score": 1,
                "expected_comment": "Точное совпадение"
            },
            {
                "case_name": "Only negative num",
                "given": "-123",
                "reference": "-123",
                "expected_score": 1,
                "expected_comment": "Точное совпадение"
            },
            {
                "case_name": "Word with digit",
                "given": "ответ 123",
                "reference": "ответ 123",
                "expected_score": 1,
                "expected_comment": "Точное совпадение"
            },
            {
                "case_name": "Different case",
                "given": "ТоЧнЫй ОтВеТ",
                "reference": "точный ответ",
                "expected_score": 1,
                "expected_comment": "Точное совпадение"
            },
            {
                "case_name": "Digit around text",
                "given": "ответ x 1 y",
                "reference": "ответ x 1 y",
                "expected_score": 1,
                "expected_comment": "Точное совпадение"
            },
            {
                "case_name": "Different punct/splitters",
                "given": "[1:2/3(4)]",
                "reference": "1.2.3.4",
                "expected_score": 1,
                "expected_comment": "Точное совпадение"
            },
            {
                "case_name": "Mismatch spaces, punct and special symbols",
                "given": "\tточный?\nответ!   ",
                "reference": "точный ответ",
                "expected_score": 1,
                "expected_comment": "Точное совпадение"
            },
            {
                "case_name": "Hyphen as a splitter",
                "given": "точный ответ",
                "reference": "точный-ответ",
                "expected_score": 1,
                "expected_comment": "Точное совпадение"
            },
        ]
        for case in test_cases:
            with self.subTest(case=case["case_name"]):
                result = self.grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["expected_score"])
                self.assertEqual(result.comment, case["expected_comment"])

    def test_prefix_match(self):
        """Тестирование совпадения по префиксу"""
        test_cases = [
            {
                "case_name": "Full, different case, unnecessary word",
                "given": "ОтВеТ пРавИльНый",
                "reference": "ответ",
                "expected_score": 1,
                "expected_comment": "Является префиксом эталона"
            },
            {
                "case_name": "Full, puncts, spaces and unnecessary word",
                "given": "\t?ответ\nправильный*)",
                "reference": "правильный",
                "expected_score": 1,
                "expected_comment": "Является префиксом эталона"
            },
            {
                "case_name": "Full with unnecessary digit",
                "given": "ответ 123",
                "reference": "ответ",
                "expected_score": 1,
                "expected_comment": "Является префиксом эталона"
            },
            {
                "case_name": "Full with repeated digit",
                "given": "123 ответ 123",
                "reference": "123 ответ",
                "expected_score": 1,
                "expected_comment": "Является префиксом эталона"
            },
            {
                "case_name": "Partial, one word",
                "given": "эт",
                "reference": "это",
                "expected_score": 1,
                "expected_comment": "Является префиксом эталона"
            },
            {
                "case_name": "Partial, multiple words",
                "given": "эт пр",
                "reference": "это пример",
                "expected_score": 1,
                "expected_comment": "Является префиксом эталона"
            },
        ]
        for case in test_cases:
            with self.subTest(case=case["case_name"]):
                result = self.grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["expected_score"])
                self.assertEqual(result.comment, case["expected_comment"])

    def test_fuzzy_match(self):
        test_cases = [
            {
                "case_name": "Partial similar",
                "given": "частично похожий ответ",
                "reference": "совсем другой ответ",
                "expected_score": 0,
                "expected_comment": "Недостаточное соответствие: текущее - 58.82%, порог - 82.30%, эталон: 'совсем другой ответ'"

            },
            {
                "case_name": "Single word fuzzy pass",
                "given": "тэстовый",
                "reference": "тестовый",
                "expected_score": 1,
                "expected_comment": "Достаточное соответствие: текущее - 87.50%, порог - 87.15%"
            },
            {
                "case_name": "Single word fuzzy fail",
                "given": "тест",
                "reference": "привет",
                "expected_score": 0,
                "expected_comment": "Недостаточное соответствие: текущее - 66.67%, порог - 87.15%, эталон: 'привет'"
            },
            {
                "case_name": "Two words barely pass",
                "given": "пример тест",
                "reference": "примэр тест",
                "expected_score": 1,
                "expected_comment": "Достаточное соответствие: текущее - 90.91%, порог - 84.31%"
            },
            {
                "case_name": "Two words barely fail",
                "given": "прурэр тест",
                "reference": "пример тест",
                "expected_score": 0,
                "expected_comment": "Недостаточное соответствие: текущее - 73.68%, порог - 84.31%, эталон: 'пример тест'"
            },
            {
                "case_name": "Fuzzy fail with digits",
                "given": "похожий ответ 123",
                "reference": "исходный ответ 123",
                "expected_score": 0,
                "expected_comment": "Недостаточное соответствие: текущее - 78.79%, порог - 82.30%, эталон: 'исходный ответ 123'"

            },
            {
                "case_name": "Fuzzy pass with digits",
                "given": "тестовый сложный пример 999 - мои ценные указания",
                "reference": "тестовый пример 999",
                "expected_score": 1,
                "expected_comment": "Достаточное соответствие: текущее - 78.95%, порог - 77.44%"
            },
            {
                "case_name": "Fuzzy pass with digits",
                "given": "тестовый пример 999",
                "reference": "тестовый сложный пример 999",
                "expected_score": 0,
                "expected_comment": "Недостаточное соответствие: текущее - 81.25%, порог - 82.30%, эталон: 'тестовый сложный пример 999'"
            },
            {
                "case_name": "Wrong prefix, high fuzzy",
                "given": "неправильный ответ",
                "reference": "правильный ответ",
                "expected_score": 1,
                "expected_comment": "Достаточное соответствие: текущее - 100.00%, порог - 84.31%"
            },
            {
                "case_name": "Long text floor threshold pass",
                "given": "Хслово " * 25,
                "reference": "слово " * 25,
                "expected_score": 1,
                "expected_comment": "Достаточное соответствие: текущее - 85.91%, порог - 70.00%"
            },
            {
                "case_name": "Almost exact match",
                "given": "ТОЧНый ответ",
                "reference": "точный отвеt",
                "expected_score": 1,
                "expected_comment": "Достаточное соответствие: текущее - 95.65%, порог - 84.31%"
            },
        ]
        """Тестирование нечеткого соответствия"""
        for case in test_cases:
            with self.subTest(case=case["case_name"]):
                result = self.grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["expected_score"])
                self.assertEqual(result.comment, case["expected_comment"])
