import uuid
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.models.template_element import TemplateElement
from labstructanalyzer.schemas.template_element import TemplateElementResponse


class NewAnswerData(BaseModel):
    element_id: uuid.UUID
    score: Optional[float] = None
    data: Optional[dict] = None
    pre_grade: Optional[dict] = None

    @staticmethod
    def from_domain(element: TemplateElementResponse, answer: Optional[Answer] = None) -> "NewAnswerData":
        return NewAnswerData(
            element_id=element.id,
            score=answer.score if answer else None,
            data=answer.data if answer else None,
            pre_grade=answer.pre_grade if answer else None
        )


class UpdateAnswerDataRequest(BaseModel):
    id: uuid.UUID
    data: Optional[dict] = None


class UpdateAnswerScoresRequest(BaseModel):
    id: uuid.UUID
    score: Optional[float] = 0


class AnswerResponse(BaseModel):
    element_id: uuid.UUID
    score: Optional[float] = None
    data: Optional[dict] = None

    id: Optional[uuid.UUID] = Field(default=None, exclude=True)
    custom_id: Optional[str] = Field(default=None, exclude=True)
    weight: Optional[float] = Field(default=None, exclude=True)
    reference: Optional[str] = Field(default=None, exclude=True)
    root_id: Optional[uuid.UUID] = Field(default=None, exclude=True)

    @staticmethod
    def find_root(element_id: uuid.UUID, elements_map: dict[uuid, Optional[TemplateElement]]) -> uuid.UUID:
        current_id = element_id
        visited = set()

        while current_id in elements_map:
            if current_id in visited:
                break

            visited.add(current_id)
            current = elements_map[current_id]

            if not current or not current.parent_element_id:
                break

            current_id = current.parent_element_id

        return current_id

    @staticmethod
    def from_domain(
            answer_model: Answer,
            elements_by_id_map: dict[uuid, Optional[TemplateElement]],
    ) -> "AnswerResponse":
        element = elements_by_id_map[answer_model.element_id]

        return AnswerResponse(
            id=answer_model.element_id,
            element_id=answer_model.element_id,
            score=answer_model.score,
            data=answer_model.data,
            custom_id=element.properties.get("customId"),
            weight=element.properties.get("weight"),
            reference=element.properties.get("refAnswer"),
            root_id=AnswerResponse.find_root(answer_model.element_id, elements_by_id_map)
        )


class PreGradedAnswerResponse(AnswerResponse):
    pre_grade: Optional[dict] = None

    @staticmethod
    def from_domain(
            answer_model: Answer,
            elements_by_id_map: dict[uuid, Optional[TemplateElement]],
    ) -> "PreGradedAnswerResponse":
        base_dto = AnswerResponse.from_domain(answer_model, elements_by_id_map)
        return PreGradedAnswerResponse(
            **base_dto.model_dump(),
            pre_grade=answer_model.pre_grade
        )

    @staticmethod
    def from_response(answer: AnswerResponse, pre_grade_result: dict):
        return PreGradedAnswerResponse(
            **answer.model_dump(),
            pre_grade=pre_grade_result
        )


@dataclass
class GradeResult:
    score: float
    comment: Optional[str] = None
    wrong_params: list[str] = None
