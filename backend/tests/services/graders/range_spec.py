import unittest
from typing import Union, Tuple

from labstructanalyzer.services.graders.range_spec import RangeSpec

Numeric = Union[int, float]
NumericPart = Union[Numeric, Tuple[Numeric, Numeric]]
Part = Union[NumericPart, str]


class TestRangeSpec(unittest.TestCase):
    def test_parsing_and_values(self):
        """Проверяем, что строка корректно парсится в parts и values"""
        cases = [
            {
                "name": "Integer range",
                "raw": "1-3",
                "parts": [(1, 3)],
                "values": [1, 2, 3]
            },
            {
                "name": "Float range",
                "raw": "1.5 - 2.5",
                "parts": [(1.5, 2.5)],
                "values": [1.5, 2.5]
            },
            {
                "name": "Integer alternatives",
                "raw": "2|4|6",
                "parts": [2, 4, 6],
                "values": [2, 4, 6]
            },
            {
                "name": "Mixed: string + int + float",
                "raw": "foo | 3 | 3.5",
                "parts": ["foo", 3, 3.5],
                "values": ["foo", 3, 3.5]
            },
            {
                "name": "String alternatives",
                "raw": " YES | no ",
                "parts": ["YES", "no"],
                "values": ["YES", "no"]
            },
            {
                "name": "Empty raw string",
                "raw": "",
                "parts": [],
                "values": []
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                spec = RangeSpec.from_raw(case["raw"])
                self.assertEqual(spec.parts, case["parts"])
                self.assertEqual(spec.values, case["values"])

    def test_property_flags(self):
        """Проверяем флаги is_numeric, is_float, is_mixed"""
        cases = [
            {
                "name": "Integer range",
                "raw": "1-5",
                "is_numeric": True,
                "is_float": False,
                "is_mixed": False
            },
            {
                "name": "Float range",
                "raw": "1.0-2.5",
                "is_numeric": True,
                "is_float": True,
                "is_mixed": False
            },
            {
                "name": "Strings only",
                "raw": "a|b|c",
                "is_numeric": False,
                "is_float": False,
                "is_mixed": False
            },
            {
                "name": "Mixed string and number",
                "raw": "x|3",
                "is_numeric": False,
                "is_float": False,
                "is_mixed": True
            },
            {
                "name": "Empty spec",
                "raw": "", "is_numeric":
                True, "is_float": False,
                "is_mixed": False
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                spec = RangeSpec.from_raw(case["raw"])
                self.assertEqual(spec.is_numeric, case["is_numeric"])
                self.assertEqual(spec.is_float, case["is_float"])
                self.assertEqual(spec.is_mixed, case["is_mixed"])

    def test_regex_fragment_generation(self):
        """Проверяем, что возвращается корректный фрагмент regex"""
        cases = [
            {
                "name": "Integers only",
                "raw": "1|2|3",
                "fragment": r"(-?\d+)"
            },
            {
                "name": "Floats",
                "raw": "1.0|2.5",
                "fragment": r"(-?\d+(?:\.\d+)?)"
            },
            {
                "name": "Integer range",
                "raw": "5-10",
                "fragment": r"(-?\d+)"
            },
            {
                "name": "Float range",
                "raw": "0.5-1.5",
                "fragment": r"(-?\d+(?:\.\d+)?)"
            },
            {
                "name": "Strings only",
                "raw": "foo|bar",
                "fragment": r"(\S+)"
            },
            {
                "name": "Mixed int and string",
                "raw": "a|1",
                "fragment": r"(\S+)"
            },
            {
                "name": "Empty",
                "raw": "",
                "fragment": r"(-?\d+)"
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                spec = RangeSpec.from_raw(case["raw"])
                self.assertEqual(spec.regex_fragment(), case["fragment"])

    def test_match(self):
        """Проверяем, что match() корректно определяет допустимые значения"""
        cases = [
            {
                "name": "Integer range",
                "raw": "1-5",
                "yes": ["1", "3", "5"],
                "no": ["0", "6", "a"]
            },
            {
                "name": "Float range",
                "raw": "-1.0 - 1.0",
                "yes": ["-1.0", "0", "1", "1.0"],
                "no": ["-1.1", "1.1", "foo"]
            },
            {
                "name": "Integer alternatives",
                "raw": "2|4|6",
                "yes": ["2", "4", "6"],
                "no": ["1", "3", ""]
            },
            {
                "name": "Case-insensitive strings",
                "raw": "Yes|no",
                "yes": ["yes", "NO", "YeS"],
                "no": ["y", "n", "maybe"]
            },
            {
                "name": "Mixed values",
                "raw": "a|3.5|b",
                "yes": ["a", "3.5", "b"],
                "no": ["c", "3", "4.0", ""]
            },
            {
                "name": "Single integer",
                "raw": "42", "yes": ["42"],
                "no": ["41", "43", "foo"]
            },
            {
                "name": "Single float",
                "raw": "3.14",
                "yes": ["3.14", "3.140", "3.1400"],
                "no": ["3.1", "foo"]
            },
            {
                "name": "Empty spec match",
                "raw": "",
                "yes": [],
                "no": ["", "1", "foo"]
            },
        ]

        for case in cases:
            spec = RangeSpec.from_raw(case["raw"])
            for val in case["yes"]:
                with self.subTest(f"{case['name']} → match '{val}'"):
                    self.assertTrue(spec.match(val))
            for val in case["no"]:
                with self.subTest(f"{case['name']} → no match '{val}'"):
                    self.assertFalse(spec.match(val))

    def test_numeric_equivalence(self):
        """Проверяем, что float и int с равным значением считаются совпадающими"""
        cases = [
            {"raw": "3", "input": "3.0", "expected": True},
            {"raw": "3.0", "input": "3", "expected": True},
            {"raw": "3 | 4.0", "input": "4", "expected": True},
            {"raw": "3 | 4.0", "input": "4.0", "expected": True},
            {"raw": "3.5", "input": "3", "expected": False},
            {"raw": "3", "input": "3.5", "expected": False},
        ]

        for case in cases:
            with self.subTest(f"{case['raw']} vs {case['input']}"):
                spec = RangeSpec.from_raw(case["raw"])
                self.assertEqual(spec.match(case["input"]), case["expected"])

    def test_from_raw_cache(self):
        """Проверяем, что from_raw кэширует экземпляры"""
        a = RangeSpec.from_raw("1-5")
        b = RangeSpec.from_raw("1-5")
        c = RangeSpec.from_raw("2-4")

        with self.subTest("Same raw returns same object"):
            self.assertIs(a, b)
        with self.subTest("Different raw returns different object"):
            self.assertIsNot(a, c)


if __name__ == "__main__":
    unittest.main()
