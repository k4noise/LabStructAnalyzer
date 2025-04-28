import re
from rapidfuzz import fuzz
from labstructanalyzer.models.dto.answer import GradeResult
from labstructanalyzer.services.graders.abstract_base import BaseGrader


class FixedAnswerGrader(BaseGrader):
    _RE_WORDS = re.compile(r'[a-zа-яёй]+')
    _RE_DIGITS = re.compile(r'\d+')

    def grade(self, given_answer: str, reference_answer: str) -> GradeResult:
        reference_words, reference_digits = self._split_alnum(reference_answer)
        given_words, given_digits = self._split_alnum(given_answer)

        if given_digits != reference_digits:
            return GradeResult(
                score=0,
                comment=f"Цифры не совпадают. Эталон: {reference_answer}, Ответ: {given_answer}"
            )

        if given_words == reference_words:
            return GradeResult(score=1)

        if len(given_words) <= len(reference_words):
            for offset in range(len(reference_words) - len(given_words) + 1):
                if all(reference_words[offset + i].startswith(given_words[i])
                       for i in range(len(given_words))):
                    return GradeResult(score=1)

        score = fuzz.ratio(given_words, reference_words)
        if score >= 90:
            return GradeResult(score=1)

        return GradeResult(
            score=0,
            comment=f"Низкое совпадение слов. Схожесть: {score}%, Эталон: {reference_answer}, Ответ: {given_answer}"
        )

    def _split_alnum(self, answer: str) -> tuple[list[str], list[str]]:
        answer = answer.lower()
        letters = self._RE_WORDS.findall(answer)
        digits = self._RE_DIGITS.findall(answer)
        return letters, digits
