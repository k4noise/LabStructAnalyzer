import copy
from collections import deque
from typing import Generator, Optional
from labstructanalyzer.utils.parser.base_definitions import IParserElement
from labstructanalyzer.utils.parser.common_elements import QuestionElement, AnswerElement
from labstructanalyzer.utils.parser.structure.checkers import CheckerRegistry
from labstructanalyzer.utils.parser.structure.structure_components import BaseStructureComponent, \
    CompositeStructureComponent


class StructureManager:
    """Работает с элементами парсера, приводя их к единой структуре
    """

    def __init__(self, structure: dict):
        """Инициализирует StructureManager с переданной структурой JSON.

        Args:
            structure: Словарь, определяющий структуру JSON. Должен содержать ключи "answer", "base", и "composite".

        Raises:
            TypeError: Если структура JSON неверна.
        """
        if not all(key in structure for key in ["answer", "base", "composite"]):
            raise TypeError("Wrong JSON structure")

        self.checkers = CheckerRegistry()
        self.checkers.create_direct("hasProperty",
                                    lambda element, expected: element.to_dict().get(expected) is not None)
        self.checkers.create_common("headerLevel", "header_level",
                                    lambda current, expected: str(current) == str(expected))
        self.checkers.create_common("hasStyle", "style_id", lambda current, expected: current == expected)
        self.checkers.create_common("startsWith", "data", lambda current, expected: current.startswith(expected))

        self.answer_delimiter = structure["answer"]["charDelimiter"] * structure["answer"]["minRepeatCount"]
        self.base = {json_part["type"]: BaseStructureComponent(self.checkers, json_part) for json_part in
                     structure["base"]}
        self.composite = [CompositeStructureComponent(self.checkers, json_part) for json_part in structure["composite"]]

        self.max_chunk_count = max(validator.chunk_count for validator in self.composite)

    def apply(self, elements: Generator[IParserElement, None, None]) -> Generator[dict, None, None]:
        """Применяет структуру ко всем элементам парсера из генератора

        Args:
            elements: Генератор объектов IParserElement

        Yields:
            Словари, представляющие структурированные элементы для сериализации в JSON
        """
        chunk: deque[IParserElement] = deque(maxlen=self.max_chunk_count)

        for item in elements:
            for base in self.base.values():
                if base.validate(item):
                    item.structure_type = base.structure_type
                    if self.contain_answer_mark(item):
                        item.structure_type = "question"
                    break

            chunk.append(item)

            while len(chunk) == self.max_chunk_count:
                for composite in self.composite:
                    if composite.validate(list(chunk)):
                        composite_element = composite.get_structure_template()
                        composite_element["data"] = [
                            self.recursive_apply_structure(child_element) for child_element in
                            list(chunk)[:composite.chunk_count]
                        ]
                        yield composite_element
                        for _ in range(composite.chunk_count):
                            chunk.popleft()
                        break
                else:
                    current_element = chunk.popleft()
                    next_element = chunk[0] if len(chunk) else None
                    if current_element.structure_type == "text" and self.is_only_answer_mark(next_element):
                        current_element.structure_type = "question"
                        current_element.data += next_element.data
                        chunk.popleft()
                    structured_element = self.recursive_apply_structure(current_element)
                    yield structured_element

        while chunk:
            yield self.recursive_apply_structure(chunk.popleft())

    def recursive_apply_structure(self, element: IParserElement) -> dict:
        """Рекурсивно применяет структуру к элементу парсера

        Args:
            element: Объект IParserElement

        Returns:
            Словарь, представляющий структурированный элемент
        """
        structure_type = element.structure_type if hasattr(element, "structure_type") else None

        if structure_type is None:
            for base in self.base.values():
                if base.validate(element):
                    element.structure_type = base.structure_type
                    break

        if structure_type == "question":
            element = self.extract_question_from_text(element)

        element_dict = self.base[structure_type].apply_structure(element) if structure_type else element.to_dict()
        element_dict["data"] = self.recursive_apply_structure_in_child(element.data)
        return element_dict

    def recursive_apply_structure_in_child(self, element) -> dict | list[dict] | None:
        """Рекурсивно применяет структуру к потомкам элемента

        Args:
            element: Потомок элемента (может быть IParserElement, list или другой тип данных)

        Returns:
            Словарь, список словарей или None, представляющий структурированного потомка
        """
        if isinstance(element, list):
            return [self.recursive_apply_structure_in_child(item) for item in element]

        if not isinstance(element, IParserElement):
            return element

        if self.contain_answer_mark(element):
            answer_template = self.extract_answer_template(element)
            return self.recursive_apply_structure(
                self.create_answer_element(element.nesting_level, answer_template)
            )

        return self.recursive_apply_structure(element)

    def create_answer_element(self, nesting_level: Optional[int], answer_template: Optional[str]) -> AnswerElement:
        """Создает элемент "Ответ"

        Args:
            nesting_level: Уровень вложенности родительского элемента
            answer_template: Шаблон для заполнения ответа

        Returns:
            Элемент "Ответ"
        """
        answer_element = AnswerElement(answer_template)
        answer_element.structure_type = "answer"
        if nesting_level:
            answer_element.nesting_level = nesting_level
        return answer_element

    def contain_answer_mark(self, element: IParserElement) -> bool:
        """
        Проверяет, содержит ли элемент метку ответа

        Args:
            element: Объект IParserElement

        Returns:
            True, если элемент содержит метку ответа, иначе False
        """
        if element.element_type.value != "text":
            return False
        return element.data.find(self.answer_delimiter) >= 0

    def is_only_answer_mark(self, element: IParserElement):
        """Проверяет, состоит ли элемент только из метки ответа

        Args:
            element: Объект IParserElement

        Returns:
            True, если элемент состоит только из метки ответа, иначе False
        """
        if element.element_type.value != 'text':
            return False
        return element.data.find(self.answer_delimiter) == 0

    def extract_question_from_text(self, element: IParserElement):
        """Извлекает вопрос и создает элемент ответа из текстового элемента

        Args:
            element: Объект IParserElement

        Returns:
            Элемент вопроса или None, если текст не содержит метки вопроса
        """
        index = element.data.find(self.answer_delimiter)
        question_text_component = element.data[:index].strip()
        answer_template = self.extract_answer_template(element)

        text_component = copy.deepcopy(element)
        text_component.data = question_text_component
        text_component.structure_type = "text"

        answer_component = self.create_answer_element(None, answer_template)

        question_element = QuestionElement(data=[
            text_component,
            answer_component
        ])
        question_element.structure_type = "question"
        question_element.nesting_level = element.nesting_level
        return question_element

    def extract_answer_template(self, element: IParserElement):
        """Извлекает шаблон ответа из элемента

        Args:
            element: Объект IParserElement

        Returns:
            Шаблон ответа или None, если шаблон ответа не найден
        """
        index = element.data.rfind(self.answer_delimiter)
        template = element.data[index + len(self.answer_delimiter):]
        return template.strip() if template else None
