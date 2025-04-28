from abc import ABC, abstractmethod
from labstructanalyzer.models.dto.answer import GradeResult


class BaseGrader(ABC):
    @abstractmethod
    def grade(self, given_answer: str, reference_answer: str) -> GradeResult:
        pass
