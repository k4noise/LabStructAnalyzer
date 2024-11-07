import uuid
from collections import deque
from typing import Generator
from labstructanalyzer.utils.parser.base_definitions import IParserElement
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

    def apply_structure(self, elements: Generator[IParserElement, None, None]) -> Generator[dict, None, None]:
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
                        item.structure_type = "QnA"
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
                    structured_element = self.recursive_apply_structure(chunk.popleft())
                    if structured_element.get("type") == "question":
                        structured_element.pop("answer_template", None)
                        yield structured_element
                        yield self.create_answer_dict(structured_element.get("nestingLevel"),
                                                      structured_element.get("answer_template"))
                        continue
                    elif chunk[0].structure_type == "QnA" and self.is_only_answer_mark(chunk[0]):
                        structured_element["type"] = "question"
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
        if element.structure_type == "QnA":
            question_text = self.extract_question_text(element)
            answer_template = self.extract_answer_template(element)

            if question_text:
                element.structure_type = "question"
                element.data = question_text
                question_element = self.base["question"].apply_structure(element)
                if answer_template:
                    question_element["answer_template"] = answer_template
                return question_element

            return self.create_answer_dict(element.nesting_level, answer_template)

        if element.structure_type is None:
            for base in self.base.values():
                if base.validate(element):
                    element.structure_type = base.structure_type
                    break

        element_dict = self.base[element.structure_type].apply_structure(element)
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
            return self.create_answer_dict(element.nesting_level, answer_template)
        return self.recursive_apply_structure(element)

    def create_answer_dict(self, nesting_level: int, answer_template: str) -> dict:
        """Создает словарь для элемента "Ответ"

        Args:
            nesting_level: Уровень вложенности родительского элемента
            answer_template: Шаблон для заполнения ответа

        Returns:
            Словарь с данными элемента "Ответ"
        """
        answer_dict = {"type": "answer", "contentType": "answer", "id": uuid.uuid4().hex}
        if nesting_level:
            answer_dict["nestingLevel"] = nesting_level
        if answer_template:
            answer_dict["template"] = answer_template
        return answer_dict

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
        return element.data.find(self.answer_delimiter) == 0

    def extract_question_text(self, element: IParserElement):
        """Извлекает текст вопроса из элемента

        Args:
            element: Объект IParserElement

        Returns:
            Текст вопроса или None, если текст вопроса не найден
        """
        index = element.data.find(self.answer_delimiter)
        question_text = element.data[:index]
        return question_text.strip() if question_text else None

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
