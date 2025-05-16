import unittest
from unittest.mock import patch, Mock
import numpy as np

from labstructanalyzer.services.graders.argument import ArgumentAnswerGrader

patch_morph = patch('labstructanalyzer.services.graders.argument.MorphAnalyzer')
MockMorphAnalyzer = patch_morph.start()

mock_morph_instance = Mock()
mock_morph_instance.parse.side_effect = lambda word: [Mock(normal_form=word.lower(), tag=Mock(POS='NOUN'))]
MockMorphAnalyzer.return_value = mock_morph_instance

VECTOR_SIZE = 300


class TestArgumentAnswerGrader(unittest.TestCase):
    """
    Юнит-тесты для ArgumentAnswerGrader.

    Тестирует логику оценки ответов на основе семантической близости тезисов,
    смоделированной с помощью моков внешних зависимостей (NewsEmbedding, MorphAnalyzer).

    Зоопарк моков и данных:
    - NewsEmbedding мокается для каждого теста с использованием `@patch`.
    - Его метод `get()` мокается локально в каждом тесте с помощью `side_effect`.
    - Поведение `side_effect` определяется словарем `local_word_vectors`,
      который маппит слова (или их леммы) на тестовые векторы.
    - Для тестов с ожидаемым score=1 используются коллинеарные векторы (`[X]*VECTOR_SIZE`),
      которые дают идеальное косинусное сходство (1.0) для одинаковых векторов.
    - Для тестов с ожидаемым score < 1 или score=0 используются ортогональные векторы
      (`np.eye(VECTOR_SIZE)[i]`), которые дают низкое косинусное сходство (0.0 raw, 0.5 transformed)
      между разными векторами, имитируя семантически далекие концепты.
    - MorphAnalyzer мокается глобально для всего класса, чтобы обеспечить быструю инициализацию
      ArgumentAnswerGrader без реальной модели. Его мок имитирует базовую лемматизацию
      (нижний регистр) и определение части речи (всегда NOUN).
    """

    @classmethod
    def tearDownClass(cls):
        if 'MockMorphAnalyzer' in globals():
            patch_morph.stop()

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_exact_semantic_match(self, mock_embedding_cls):
        """
        Тестирует точное семантическое совпадение переформулированных тезисов.
        Моки векторов настроены так, чтобы семантически близкие слова мапились
        на одинаковые коллинеарные векторы.
        """
        vec_technology = np.array([0.1] * VECTOR_SIZE)
        vec_industry = np.array([0.2] * VECTOR_SIZE)
        vec_education = np.array([0.3] * VECTOR_SIZE)

        local_word_vectors = {
            'развитие': vec_technology, 'технология': vec_technology,
            'развиваться': vec_technology, 'стремительно': vec_technology,
            'поддержка': vec_industry, 'промышленность': vec_industry,
            'индустрия': vec_industry, 'нужно': None, 'поддерживать': vec_industry,
            'образование': vec_education, 'будущий': vec_education,
            'современный': vec_education, 'общество': vec_education,
        }

        def get_word_vector_side_effect(word):
            return local_word_vectors.get(word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance

        grader = ArgumentAnswerGrader()

        reference = "Развитие технологий. Поддержка промышленности. Образование будущего."
        given = "Технологии развиваются стремительно. Индустрию нужно поддерживать. Современному обществу нужно образование."

        result = grader.grade(given, reference)
        self.assertEqual(result.score, 1.0)
        self.assertIsNone(result.comment)

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_literal_match_different_order(self, mock_embedding_cls):
        """
        Тестирует дословное совпадение тезисов в другом порядке предложений.
        Моки векторов настроены так, чтобы каждое ключевое слово мапилось на
        уникальный коллинеарный вектор.
        """
        vec_economy = np.array([0.1] * VECTOR_SIZE)
        vec_security = np.array([0.2] * VECTOR_SIZE)
        vec_will = np.array([0.3] * VECTOR_SIZE)

        local_word_vectors = {
            'экономика': vec_economy,
            'безопасность': vec_security,
            'воля': vec_will,
        }

        def get_word_vector_side_effect(word):
            return local_word_vectors.get(word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        ref = "Экономика. Безопасность. Воля."
        given = "Безопасность. Воля. Экономика."

        result = grader.grade(given, ref)
        self.assertEqual(result.score, 1.0)
        self.assertIsNone(result.comment)

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_normalization_effects(self, mock_embedding_cls):
        """
        Тестирует, что разные регистры и пробелы не влияют на оценку.
        Мок имитирует, что грейдер правильно нормализует текст
        перед получением векторов, выполняя маппинг слов в нижнем регистре на векторы.
        """
        vec_human_capital = np.array([0.1] * VECTOR_SIZE)
        vec_energy_efficiency = np.array([0.2] * VECTOR_SIZE)

        local_word_vectors = {
            'человеческий': vec_human_capital,
            'капитал': vec_human_capital,
            'энергоэффективность': vec_energy_efficiency,
        }

        def get_word_vector_side_effect(word):
            return local_word_vectors.get(word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        reference = "Человеческий Капитал. Энергоэффективность."
        given = "человеческий     капитал.   Энергоэффективность"

        result = grader.grade(given, reference)
        self.assertEqual(result.score, 1.0)

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_empty_reference(self, mock_embedding_cls):
        """Тестирует случай пустого эталона reference"""
        embedding_instance = Mock()
        embedding_instance.get.side_effect = lambda w: None
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        result = grader.grade("что угодно", "")
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.comment, "Эталон пуст")

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_empty_given(self, mock_embedding_cls):
        """Тестирует случай пустого ответа answer"""
        embedding_instance = Mock()
        embedding_instance.get.side_effect = lambda w: None
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        result = grader.grade("", "Один тезис")
        self.assertEqual(result.score, 0)
        self.assertIsNone(result.comment)

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_some_reference_theses_not_matched(self, mock_embedding_cls):
        """
        Тестирует случай, когда не все тезисы reference найдены в answer.
        Моки векторов настроены так, чтобы
        только часть тезисов reference имела высокое сходство с предложениями given.
        Для разных концептов используются ортогональные векторы, дающие низкое сходство.
        """
        vec_ecology = np.eye(VECTOR_SIZE)[0]
        vec_economy = np.eye(VECTOR_SIZE)[1]
        vec_education = np.eye(VECTOR_SIZE)[2]

        local_word_vectors = {
            'экология': vec_ecology,
            'экономика': vec_economy,
            'образование': vec_education,
            'важна': vec_economy,
        }

        def get_word_vector_side_effect(word):
            return local_word_vectors.get(word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        reference = "Экология. Экономика. Образование."
        given = "Экономика важна."

        result = grader.grade(given, reference)
        self.assertGreater(result.score, 0)
        self.assertLess(result.score, 1)
        self.assertIsNotNone(result.comment)
        self.assertEqual(result.comment, 'Тезисы не найдены: Экология; Образование')

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_no_thesis_match(self, mock_embedding_cls):
        """
        Тестирует случай полного отсутствия совпадений между answer и reference.
        Моки векторов настроены так, чтобы все предложения given
        имели низкое сходство с любым тезисом reference.
        Для разных концептов используются ортогональные векторы.
        """
        vec_ref1 = np.eye(VECTOR_SIZE)[0]
        vec_ref2 = np.eye(VECTOR_SIZE)[1]
        vec_ref3 = np.eye(VECTOR_SIZE)[2]
        vec_given = np.eye(VECTOR_SIZE)[3]

        local_word_vectors = {
            'цифровизация': vec_ref1, 'индустрия': vec_ref2, 'переработка': vec_ref3,
            'кот': vec_given, 'есть': vec_given, 'мышь': vec_given,
        }

        def get_word_vector_side_effect(word):
            return local_word_vectors.get(word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        reference = "Цифровизация. Индустрия. Переработка."
        given = "Коты едят мышей."

        result = grader.grade(given, reference)
        self.assertEqual(result.score, 0)
        self.assertEqual(result.comment, 'Тезисы не найдены: Цифровизация; Индустрия; Переработка')

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_repeating_words_dont_fool_grader(self, mock_embedding_cls):
        """
        Тестирует, что многократное повторение слов, относящихся только к части тезисов,
        не приводит к score 1.
        Моки векторов настроены так, чтобы "Космос" и "Биология" мапились
        на разные ортогональные векторы.
        """
        reference = "Космос. Биология."

        vec_space = np.eye(VECTOR_SIZE)[0]
        vec_biology = np.eye(VECTOR_SIZE)[1]

        local_word_vectors = {
            'космос': vec_space,
            'биология': vec_biology,
        }

        def get_word_vector_side_effect(word):
            return local_word_vectors.get(word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        given = "Космос космос космос космос космос"

        result = grader.grade(given, reference)
        self.assertGreater(result.score, 0)
        self.assertLess(result.score, 1)
        self.assertEqual(result.comment, "Тезисы не найдены: Биология")

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_partial_sentence_match(self, mock_embedding_cls):
        """
        Тестирует случай, когда часть предложений answer соответствует тезисам reference,
        а часть - нет.
        Моки векторов настроены так, чтобы часть
        предложений given соответствовала тезисам reference (высокое сходство),
        а часть - не соответствовала (низкое сходство).
        Для разных концептов используются ортогональные векторы.
        """
        vec_a = np.eye(VECTOR_SIZE)[0]
        vec_b = np.eye(VECTOR_SIZE)[1]
        vec_v = np.eye(VECTOR_SIZE)[2]
        vec_other = np.eye(VECTOR_SIZE)[3]

        local_word_vectors = {
            'а': vec_a,
            'б': vec_b,
            'в': vec_v,
            'нечто': vec_other,
            'совсем': vec_other,
            'другое': vec_other,
        }

        def get_word_vector_side_effect(word):
            cleaned_word = word.lower().strip('.')
            return local_word_vectors.get(cleaned_word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        reference = "А. Б. В."
        given = "А. Нечто совсем другое. В."

        result = grader.grade(given, reference)
        self.assertGreater(result.score, 0)
        self.assertLess(result.score, 1)
        self.assertEqual(result.comment, "Тезисы не найдены: Б")

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_given_contains_only_noise(self, mock_embedding_cls):
        """
        Тестирует случай, когда answer содержит только стоп-слова или шум.
        Моки настроены так, что для слов в answer get()
        возвращает None, приводя к нулевому вектору предложения.
        """
        vec_capital = np.eye(VECTOR_SIZE)[0]

        local_word_vectors = {
            'капитал': vec_capital,
        }

        def get_word_vector_side_effect(word):
            return local_word_vectors.get(word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        ref = "Капитал"
        given = "и в на о о у у"

        result = grader.grade(given, ref)
        self.assertEqual(result.score, 0)
        self.assertEqual(result.comment, "Тезисы не найдены: Капитал")

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_unknown_words_in_given(self, mock_embedding_cls):
        """
        Тестирует случай, когда все слова в answer не находятся в словаре векторов.
        Мок NewsEmbedding.get настроен так, чтобы всегда возвращать None.
        """
        vec_healthcare = np.eye(VECTOR_SIZE)[0]

        embedding_instance = Mock()
        embedding_instance.get.side_effect = lambda word: None
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        ref = "Здравоохранение"
        given = "абра кадабра фубара"

        result = grader.grade(given, ref)
        self.assertEqual(result.score, 0)
        self.assertEqual(result.comment, "Тезисы не найдены: Здравоохранение")

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_punctuation_ignored(self, mock_embedding_cls):
        """
        Тестирует, что пунктуация в answer не влияет на оценку при наличии совпадений.
        Мок настроен так, чтобы мапить нормализованные слова
        (без пунктуации) на коллинеарные векторы.
        """
        vec_tax_reform = np.array([0.1] * VECTOR_SIZE)

        local_word_vectors = {
            'реформа': vec_tax_reform,
            'налоговой': vec_tax_reform,
            'система': vec_tax_reform,
        }

        def get_word_vector_side_effect(word):
            return local_word_vectors.get(word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        reference = "Реформа налоговой системы"
        given = "Реформа! налоговой???? системы..."

        result = grader.grade(given, reference)
        self.assertEqual(result.score, 1)

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_sentence_order_does_not_matter(self, mock_embedding_cls):
        """
        Тестирует, что порядок предложений в answer не влияет на итоговую оценку,
        если все тезисы reference покрыты.
         Моки векторов настроены так, чтобы каждое предложение
        (или его ключевые слова) мапилось на уникальный ортогональный вектор.
        Благодаря алгоритму `_match_theses` (max сходство с любым user-вектором),
        порядок user-векторов не имеет значения.
        """
        vec_sentence_1 = np.eye(VECTOR_SIZE)[0]
        vec_sentence_2 = np.eye(VECTOR_SIZE)[1]
        vec_sentence_3 = np.eye(VECTOR_SIZE)[2]

        local_word_vectors = {
            '1': vec_sentence_1,
            '2': vec_sentence_2,
            '3': vec_sentence_3,
        }

        def get_word_vector_side_effect(word):
            cleaned_word = word.lower().strip('.')
            return local_word_vectors.get(cleaned_word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        reference = "1. 2. 3."
        given = "3. 1. 2."

        result = grader.grade(given, reference)
        self.assertEqual(result.score, 1)

    @patch("labstructanalyzer.services.graders.argument.NewsEmbedding")
    def test_additional_text_does_not_decrease_score(self, mock_embedding_cls):
        """
        Тестирует, что наличие дополнительного текста в answer не снижает score,
        если все тезисы reference покрыты.
        Моки векторов настроены так, что слова из тезисов
        reference мапятся на один вектор (или группу коллинеарных векторов),
        а слова из дополнительного текста - на другой (ортогональный) вектор или None.
        """
        vec_peace_labor = np.array([0.1] * VECTOR_SIZE)
        vec_other = np.eye(VECTOR_SIZE)[1]

        local_word_vectors = {
            'мир': vec_peace_labor,
            'труд': vec_peace_labor,
            'это': vec_other, 'важно': vec_other, 'остальное': vec_other, 'неважно': vec_other,
            'хоть': vec_other, 'котик': vec_other, 'собачка': vec_other,
        }

        def get_word_vector_side_effect(word):
            return local_word_vectors.get(word)

        embedding_instance = Mock()
        embedding_instance.get.side_effect = get_word_vector_side_effect
        mock_embedding_cls.return_value = embedding_instance
        grader = ArgumentAnswerGrader()

        reference = "Мир и труд."
        given = "Мир и труд. Это важно. Остальное неважно. Хоть котики, хоть собачки."

        result = grader.grade(given, reference)
        self.assertEqual(result.score, 1)


if __name__ == "__main__":
    if 'ArgumentAnswerGrader' in globals() and ArgumentAnswerGrader is not None and not patch_morph.is_patched:
        patch_morph.start()
        mock_morph_instance = Mock()
        mock_morph_instance.parse.side_effect = lambda word: [Mock(normal_form=word.lower(), tag=Mock(POS='NOUN'))]
        MockMorphAnalyzer.return_value = mock_morph_instance
        import atexit

        atexit.register(patch_morph.stop)

    unittest.main()
