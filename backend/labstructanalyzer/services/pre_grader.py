import re

from rapidfuzz import fuzz

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.services.answer import AnswerType


class PreGraderService:
    _RE_WORDS = re.compile(r'[a-zа-яёй]+')
    _RE_DIGITS = re.compile(r'\d+')

    def __init__(self, answers: list[Answer], template_elements: dict):
        self.answers_data = answers
        self.answer_elements = template_elements

    def grade(self):
        graded_answers = {}

        for answer in self.answers_data:
            answer_element = self.answer_elements[answer.element_id]

            if not answer.data or not "refAnswer" in answer_element.properties:
                continue

            match answer_element.properties["answerType"]:
                case AnswerType.simple.name:
                    graded_answers[answer.answer_id] = self._grade_fixed(answer.data["text"],
                                                                         answer_element.properties["refAnswer"])

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

    def _save_to_bd(self):
        pass
