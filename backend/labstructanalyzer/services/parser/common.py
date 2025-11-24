import json
import os

from starlette.datastructures import UploadFile

from labstructanalyzer.configs.config import TEMPLATE_IMAGE_PREFIX, CONFIG_DIR
from labstructanalyzer.exceptions.parser import UnsupportedFileTypeError
from labstructanalyzer.services.parser.docx import DocxParser
from labstructanalyzer.utils.parser.structure.structure_manager import StructureManager


class ParserService:
    PARSERS = {
        "docx": DocxParser
    }

    def __init__(self):
        # TODO ВНИМАНИЕ ХАРДКОД
        file_path = os.path.join(CONFIG_DIR, "structure.json")
        with open(file_path, 'r', encoding='utf-8') as file:
            structure = json.load(file)
        self.structure_manager = StructureManager(structure)

    async def get_structured_components(self, template: UploadFile) -> list[dict]:
        """Получает список всех структурных компонент документа из шаблона"""
        parser = self._get_parser(template.filename)(await template.read(), TEMPLATE_IMAGE_PREFIX)
        raw_parsed = parser.start()
        return list(self.structure_manager.apply(raw_parsed))

    def get_name(self, template: UploadFile):
        file_name_parts = os.path.splitext(os.path.basename(template.filename))
        return file_name_parts[0]

    def _get_parser(self, file_name: str):
        file_name_parts = os.path.splitext(os.path.basename(file_name))
        extension = file_name_parts[1].lower()[1:]
        if parser := self.PARSERS.get(extension):
            return parser
        raise UnsupportedFileTypeError(extension)
