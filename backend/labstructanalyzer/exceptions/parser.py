class ParserError(Exception):
    """Исключения, возникающие в ходе работы парсера"""

    def __init__(self, file_name: str):
        super().__init__(f"Ошибка парсинга файла: {file_name}")


class UnsupportedFileTypeError(ParserError):
    """Исключение для неподдерживаемого типа файла"""

    def __init__(self, file_extension: str):
        super().__init__(f"неподдерживаемый тип файла - {file_extension}")
