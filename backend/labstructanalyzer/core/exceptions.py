import uuid


class TemplateNotFoundException(Exception):
    """Исключение, возникающее при попытке доступа к несуществующему шаблону."""

    def __init__(self, template_id: uuid.UUID):
        message = f"Шаблон с ID {template_id} не найден"
        super().__init__(message)

class AgsNotSupportedException(Exception):
    """Исключение, возникающее при отсутствии доступа к службе оценок LTI 1.3"""
    def __init__(self):
        super.__init__("Нет доступа к службе оценок")