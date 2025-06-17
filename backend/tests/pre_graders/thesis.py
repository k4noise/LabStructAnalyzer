import unittest
from unittest.mock import patch, Mock
import numpy as np

from labstructanalyzer.services.graders.thesis import ThesisAnswerGrader


class TestThesisAnswerGrader(unittest.TestCase):
    def setUp(self):
        patcher_fasttext = patch('labstructanalyzer.services.graders.thesis.load_fasttext_model')
        patcher_morph = patch('labstructanalyzer.services.graders.thesis.MorphAnalyzer')

        self.mock_load_fasttext = patcher_fasttext.start()
        self.mock_morph_cls = patcher_morph.start()
        self.addCleanup(patcher_fasttext.stop)
        self.addCleanup(patcher_morph.stop)

        self.mock_morph = self.mock_morph_cls.return_value
        self.mock_morph.parse.side_effect = lambda w: [Mock(normal_form=w.lower(), tag=Mock(POS='NOUN'))]

        self.mock_model = Mock()
        self.mock_model.vector_size = 300

        def default_get_vector_behavior(word):
            vec = np.ones(300)
            return vec / np.linalg.norm(vec) if np.any(vec) else np.zeros(300)

        self.mock_model.get_vector.side_effect = default_get_vector_behavior
        self.mock_load_fasttext.return_value = self.mock_model

        self.grader = ThesisAnswerGrader()

    def _reset_mocks_to_default(self):
        """Вспомогательная функция для сброса моков к поведению по умолчанию"""

        def default_get_vector_behavior(word):
            vec = np.ones(300)
            return vec / np.linalg.norm(vec) if np.any(vec) else np.zeros(300)

        self.mock_model.get_vector.side_effect = default_get_vector_behavior
        self.mock_morph.parse.side_effect = lambda w: [Mock(normal_form=w.lower(), tag=Mock(POS='NOUN'))]

    def test_grade_empty_or_meaningless_inputs(self):
        """
        Тесты для случаев, когда входные строки пустые, содержат только пробелы
        или пунктуацию, проверяя ожидаемый балл и комментарий
        """
        cases = [
            {
                "name": "Эталон пуст, ответ содержит текст",
                "given": "текст",
                "reference": "",
                "expected_score": 1,
                "expected_comment": "Эталон пуст"
            },
            {
                "name": "Эталон пуст (пробелы), ответ содержит текст",
                "given": "текст",
                "reference": "   ",
                "expected_score": 1,
                "expected_comment": "Эталон пуст"
            },
            {
                "name": "Ответ пуст, эталон содержит текст",
                "given": "",
                "reference": "тезис",
                "expected_score": 0,
                "expected_comment": None
            },
            {
                "name": "Ответ пуст (пробелы), эталон содержит текст",
                "given": "   ",
                "reference": "тезис",
                "expected_score": 0,
                "expected_comment": None
            },
            {
                "name": "Оба пусты",
                "given": "",
                "reference": "",
                "expected_score": 1,
                "expected_comment": "Эталон пуст"
            },
            {
                "name": "Оба содержат только пробелы",
                "given": "   ",
                "reference": "   ",
                "expected_score": 1,
                "expected_comment": "Эталон пуст"
            },
        ]

        for case in cases:
            with self.subTest(name=case["name"]):
                self._reset_mocks_to_default()
                result = self.grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["expected_score"])
                self.assertEqual(result.comment, case["expected_comment"])

    def test_grade_basic_and_normalized_matching(self):
        """
        Тесты на базовое совпадение, нечувствительность к регистру,
        множественные совпадения и повторы
        """
        cases = [
            {
                "name": "Идеальное совпадение одного слова",
                "given": "тест",
                "reference": "тест",
                "expected_score": 1.0,
                "places": 5,
                "mock_effect": "default"
            },
            {
                "name": "Нечувствительность к регистру",
                "given": "важный тезис.",
                "reference": "ВАЖНЫЙ ТЕЗИС.",
                "expected_score": 1.0,
                "places": 5,
                "mock_effect": "default"
            },
            {
                "name": "Множественные совпадения для одного тезиса",
                "given": "А. А. В.",
                "reference": "А. В.",
                "expected_score": 1.0,
                "places": 5,
                "mock_effect": "default"
            },
            {
                "name": "Повторяющиеся слова в эталоне",
                "given": "Важно.",
                "reference": "Важно важно очень важно.",
                "expected_score": 1.0,
                "places": 5,
                "mock_effect": lambda w: np.ones(300) / np.linalg.norm(
                    np.ones(300)) if w.lower() == 'важно' else np.zeros(300)
            }
        ]

        for case in cases:
            with self.subTest(name=case["name"]):
                self._reset_mocks_to_default()
                if case["mock_effect"] != "default":
                    self.mock_model.get_vector.side_effect = case["mock_effect"]

                result = self.grader.grade(case["given"], case["reference"])

                self.assertAlmostEqual(result.score, case["expected_score"], places=case["places"])
                self.assertIsNone(result.comment)

    def test_grade_comment_generation_logic(self):
        """
        Тесты на генерацию комментариев: когда комментарий отсутствует
        и когда он перечисляет пропущенные тезисы
        """
        cases = [
            {
                "name": "Комментарий отсутствует, когда все тезисы найдены",
                "given": "тезис1. тезис2.",
                "reference": "тезис1. тезис2.",
                "expected_score": 1.0,
                "expected_comment": None,
                "mock_effect": "default"
            },
            {
                "name": "Комментарий перечисляет пропущенные тезисы",
                "given": "тезис1. Тезис3.",
                "reference": "тезис1. Тезис2. Тезис3.",
                "expected_score_upper_bound": 1.0,
                "expected_comment_part": "Тезис2",
                "mock_effect": lambda w: np.ones(300) / np.linalg.norm(np.ones(300)) if w.lower() in ["тезис1",
                                                                                                      "тезис3"] else np.zeros(
                    300)
            }
        ]

        for case in cases:
            with self.subTest(name=case["name"]):
                self._reset_mocks_to_default()
                if case["mock_effect"] != "default":
                    self.mock_model.get_vector.side_effect = case["mock_effect"]

                result = self.grader.grade(case["given"], case["reference"])

                if case.get("expected_comment_part"):
                    self.assertIsNotNone(result.comment)
                    self.assertIn(case["expected_comment_part"], result.comment)
                    self.assertLess(result.score, case["expected_score_upper_bound"])
                else:
                    self.assertIsNone(result.comment)
                    self.assertAlmostEqual(result.score, case["expected_score"], places=5)

    def test_grade_oov_and_error_handling(self):
        """
        Тесты на обработку слов вне словаря, нулевых векторов
        и исключений при получении векторов
        """

        def _raise_key_error(word):
            raise KeyError(f"Word '{word}' not in vocabulary")

        cases = [
            {
                "name": "OOV слова приводят к нулевой оценке",
                "given": "неизвестное слово", "reference": "тезис",
                "expected_score": 0.0, "mock_effect": lambda w: np.zeros(300)
            },
            {
                "name": "Обработка нулевых векторов - общая",
                "given": "словоа словоб", "reference": "словов словог",
                "expected_score": 0.0, "mock_effect": lambda w: np.zeros(300)
            },
            {
                "name": "Обработка нулевых векторов - самосравнение",
                "given": "слово", "reference": "слово",
                "expected_score": 0.0, "mock_effect": lambda w: np.zeros(300)
            },
            {
                "name": "Обработка исключений при получении векторов (частичные слова, разные векторы)",
                "given": "словоа ошибка словоб", "reference": "словоа ошибка словов",
                "expected_score": 0.0,
                "mock_effect": lambda w: (np.array([1.0, 0.0, 0.0] + [0.0] * 297) / np.linalg.norm(
                    np.array([1.0, 0.0, 0.0] + [0.0] * 297))) if w.lower() == 'слово1' else \
                    (np.array([0.0, 1.0, 0.0] + [0.0] * 297) / np.linalg.norm(
                        np.array([0.0, 1.0, 0.0] + [0.0] * 297))) if w.lower() == 'слово2' else \
                        (np.array([0.0, 0.0, 1.0] + [0.0] * 297) / np.linalg.norm(
                            np.array([0.0, 0.0, 1.0] + [0.0] * 297))) if w.lower() == 'слово3' else \
                            _raise_key_error(w)
            },
        ]
        for case in cases:
            with self.subTest(name=case["name"]):
                self._reset_mocks_to_default()
                self.mock_model.get_vector.side_effect = case["mock_effect"]
                result = self.grader.grade(case["given"], case["reference"])
                self.assertEqual(result.score, case["expected_score"])

    def test_grade_structural_and_encoding_properties(self):
        """
        Тесты на структурные свойства (порядок тезисов, очень длинные предложения)
        """
        cases = [
            {
                "name": "Независимость от порядка тезисов",
                "given": "Третий. Первый. Второй.",
                "reference": "Первый. Второй. Третий.",
                "expected_score": 1.0,
                "expected_comment": None,
                "mock_effect": {
                    'первый': np.array([1.0, 0.0, 0.0] + [0.0] * 297),
                    'второй': np.array([0.0, 1.0, 0.0] + [0.0] * 297),
                    'третий': np.array([0.0, 0.0, 1.0] + [0.0] * 297)
                }
            },
            {
                "name": "Очень длинные предложения",
                "given": " ".join([f"слово{i}" for i in range(50)]) + ".",
                "reference": " ".join([f"слово{i}" for i in range(50)]) + ".",
                "expected_score": 1.0,
                "expected_comment": None,
                "mock_effect": "default"
            },
        ]

        for case in cases:
            with self.subTest(name=case["name"]):
                self._reset_mocks_to_default()
                if isinstance(case["mock_effect"], dict):
                    def custom_get_vector(word):
                        vec = case["mock_effect"].get(word.lower(), np.zeros(300))
                        return vec / np.linalg.norm(vec) if np.any(vec) else np.zeros(300)

                    self.mock_model.get_vector.side_effect = custom_get_vector
                elif case["mock_effect"] == "default":
                    pass

                result = self.grader.grade(case["given"], case["reference"])

                self.assertEqual(result.score, case["expected_score"])
                self.assertEqual(result.comment, case["expected_comment"])

    def test_similarity_threshold_behavior(self):
        """
        Тест на поведение порога сходства (SIMILARITY_THRESHOLD).
        Проверяет, как изменение порога влияет на то, считается ли тезис найденным
        """
        self._reset_mocks_to_default()

        v1 = np.array([1.0, 0.0, 0.0] + [0.0] * 297)
        v2 = np.array([0.85, 0.5267, 0.0] + [0.0] * 297)

        def get_vector_for_threshold_test(word):
            if word.lower() == 'а':
                return v1
            if word.lower() == 'б':
                return v2
            return np.zeros(300)

        self.mock_model.get_vector.side_effect = get_vector_for_threshold_test

        self.grader.SIMILARITY_THRESHOLD = 0.85
        result = self.grader.grade("Б.", "А.")
        self.assertEqual(result.score, 1.0)

        self.grader.SIMILARITY_THRESHOLD = 0.86
        result = self.grader.grade("Б.", "А.")
        self.assertEqual(result.score, 0.0)

    def test_long_sentences_scoring(self):
        """
        Тест на оценку длинных предложений с семантическим сходством между словами
        """
        self._reset_mocks_to_default()

        def get_vector_for_long_sentences(word):
            mapping = {
                'инновации': np.array([1.0, 0.0, 0.0] + [0.0] * 297),
                'создание': np.array([0.8, 0.2, 0.0] + [0.0] * 297),
                'прорывных': np.array([0.8, 0.2, 0.0] + [0.0] * 297),
                'разработок': np.array([0.85, 0.15, 0.0] + [0.0] * 297),
                'обеспечивает': np.array([0.7, 0.3, 0.0] + [0.0] * 297),
                'будущее': np.array([0.0, 1.0, 0.0] + [0.0] * 297),
            }
            vec = mapping.get(word.lower(), np.zeros(300))
            return vec / np.linalg.norm(vec) if np.any(vec) else vec

        self.mock_model.get_vector.side_effect = get_vector_for_long_sentences

        ref = "Инновации в сфере технологий имеют значение."
        given = "Создание прорывных разработок обеспечивает будущее."

        result = self.grader.grade(given, ref)
        self.assertGreater(result.score, 0.7)

    def test_different_pos_tags(self):
        """
        Тест на обработку различных частей речи.
        Проверяет, что градер фильтрует слова не являющиеся существительными
        """
        self._reset_mocks_to_default()

        def mock_parse_for_pos_test(word):
            pos_mapping = {
                'бежать': 'VERB',
                'красивый': 'ADJF',
                'быстро': 'ADVB',
                'и': 'CONJ',
                'в': 'PREP',
                'слово': 'NOUN',
                'тезис': 'NOUN'
            }
            pos = pos_mapping.get(word.lower(), None)
            if pos is None:
                return [Mock(normal_form=word.lower(), tag=Mock(POS='NOUN'))]
            return [Mock(normal_form=word.lower(), tag=Mock(POS=pos))]

        self.mock_morph.parse.side_effect = mock_parse_for_pos_test

        def get_vector_for_pos_test(word):
            if word in ['бежать', 'красивый', 'быстро', 'слово', 'тезис']:
                return np.ones(300) / np.linalg.norm(np.ones(300))
            return np.zeros(300)

        self.mock_model.get_vector.side_effect = get_vector_for_pos_test

        result = self.grader.grade("слово бежать", "слово тезис")
        self.assertEqual(result.score, 1.0)

    def test_partial_thesis_matching(self):
        """
        Тест на частичное совпадение длинных тезисов,
        проверяющий способность модели находить семантически близкие слова (синонимы)
        """
        self._reset_mocks_to_default()

        def get_vector_for_partial_match(word):
            vectors = {
                'инновации': np.array([1.0, 0.1, 0.0] + [0.0] * 297),
                'новшества': np.array([0.95, 0.15, 0.0] + [0.0] * 297),
                'технологии': np.array([0.0, 1.0, 0.1] + [0.0] * 297),
                'техника': np.array([0.0, 0.9, 0.2] + [0.0] * 297),
                'важны': np.array([0.0, 0.0, 1.0] + [0.0] * 297),
                'значимы': np.array([0.1, 0.0, 0.95] + [0.0] * 297),
            }
            vec = vectors.get(word.lower(), np.zeros(300))
            return vec / np.linalg.norm(vec) if np.any(vec) else vec

        self.mock_model.get_vector.side_effect = get_vector_for_partial_match
        self.grader.SIMILARITY_THRESHOLD = 0.85

        ref = "Инновации в технологии очень важны."
        given = "Новшества в технике крайне значимы."

        result = self.grader.grade(given, ref)
        self.assertGreater(result.score, 0.8)
        self.assertIsNone(result.comment)

    def test_mixed_content_with_numbers_and_special_chars(self):
        """
        Тест на обработку смешанного контента с числами,
        словами со специальными символами и обычными словами
        """
        self._reset_mocks_to_default()

        ref = "супер-тесты стали важными."
        given = "супер-тесты стали важными."

        def get_vector_for_mixed_content(word):
            if word.lower() in ['ai-технологии', 'важными', 'стали']:
                return np.ones(300) / np.linalg.norm(np.ones(300))
            return np.zeros(300)

        self.mock_model.get_vector.side_effect = get_vector_for_mixed_content

        result = self.grader.grade(given, ref)
        self.assertGreater(result.score, 0.0)
        self.assertEqual(result.score, 1.0)


if __name__ == '__main__':
    unittest.main()
