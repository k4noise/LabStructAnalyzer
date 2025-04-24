import re

from rapidfuzz import fuzz

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.services.answer import AnswerType


class PreGraderService:
    """Сервис предварительной оценки ответов по эталонным ответам преподавателя"""
    _RE_WORDS = re.compile(r'[a-zа-яёй]+')
    _RE_DIGITS = re.compile(r'\d+')

    def __init__(self, answers: list[Answer], template_elements: dict):
        """
        Инициализирует сервис предварительной оценки

        Args:
            answers: Список ответов для оценки
            template_elements: Словарь элементов шаблона с эталонами
        """
        self.answers_data = answers
        self.answer_elements = template_elements
        self._strategies = {
            AnswerType.simple.name: self._grade_fixed
        }

    def grade(self) -> list[Answer]:
        """
        Оценивает ответы, используя соответствующие эталон из элемента шаблона.
        Обновляет поле `pre_grade` у каждого объекта `Answer` в списке

        Returns:
            Список объектов Answer с результатами оценки
        """
        for answer in self.answers_data:
            answer_element = self.answer_elements.get(answer.element_id)
            if not answer_element:
                continue

            reference_answer = answer_element.properties.get("refAnswer")
            answer_type_name = answer_element.properties.get("answerType")
            answer_text = answer.data.get("text") if answer.data else None  # Безопасное получение текста

            if not answer_text or not reference_answer or not answer_type_name:
                continue

            strategy = self._strategies.get(answer_type_name)
            if not strategy:
                continue

            score = strategy(answer_text, reference_answer)
            answer.pre_grade = {"score": score}
            if score < 1:
                answer.pre_grade["comment"] = f"Ответ не соответствует эталону {reference_answer}"
        return self.answers_data

    def _grade_fixed(self, given_answer: str, reference_answer: str) -> int:
        """
        Сравнивает данный ответ с эталонным для фиксированных ответов.
        Проверяет совпадение цифр, затем слов (точное, по префиксу или по схожести > 90%)

        Args:
            given_answer: Текст ответа пользователя
            reference_answer: Эталонный текст ответа

        Returns:
            Балл - 1, если ответ соответствует эталону, иначе - 0
        """
        reference_words, reference_digits = self._split_alnum(reference_answer)
        given_words, given_digits = self._split_alnum(given_answer)

        if given_digits != reference_digits:
            return 0
        elif given_words == reference_words:
            return 1

        if len(given_words) <= len(reference_words):
            for offset in range(len(reference_words) - len(given_words) + 1):
                if all(reference_words[offset + i].startswith(given_words[i])
                       for i in range(len(given_words))):
                    return 1

        score = fuzz.ratio(given_words, reference_words)
        return 1 if score >= 90 else 0

    def _split_alnum(self, answer: str) -> tuple[list[str], list[str]]:
        """
        Разделяет строку на список слов и список цифр

        Args:
            answer: Входная строка.

        Returns:
            Кортеж (список слов, список цифр)
        """
        answer = answer.lower()
        letters = self._RE_WORDS.findall(answer)
        digits = self._RE_DIGITS.findall(answer)
        return letters, digits
