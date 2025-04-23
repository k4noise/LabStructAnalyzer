import re

from rapidfuzz import fuzz

from labstructanalyzer.core.database import get_sync_session
from labstructanalyzer.models.answer import Answer
from labstructanalyzer.services.answer import AnswerType


class PreGraderService:
    _RE_WORDS = re.compile(r'[a-zа-яёй]+')
    _RE_DIGITS = re.compile(r'\d+')

    def __init__(self, answers: list[Answer], template_elements: dict):
        self.answers_data = answers
        self.answer_elements = template_elements
        self._strategies = {
            AnswerType.simple.name: self._grade_fixed
        }

    def grade(self):
        for answer in self.answers_data:
            answer_element = self.answer_elements.get(answer.element_id)

            if (not answer_element
                    or answer.data
                    or not answer_element.properties.get("refAnswer")):
                continue

            answer_type_name = answer_element.properties.get("answerType")
            strategy = self._strategies.get(answer_type_name)

            if not strategy:
                continue

            answer.data["preGrade"] = strategy(answer.data["text"],
                                               answer_element.properties.get("refAnswer"))
        self._save_to_bd(self.answers_data)

    def _grade_fixed(self, given_answer: str, reference_answer: str):
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

    def _split_alnum(self, answer: str):
        answer = answer.lower()
        letters = self._RE_WORDS.findall(answer)
        digits = self._RE_DIGITS.findall(answer)
        return letters, digits

    def _save_to_bd(self, answers_with_pre_grades: list[Answer]):
        for session in get_sync_session():
            for pre_graded_answer in answers_with_pre_grades:
                session.add(pre_graded_answer)
            session.commit()
