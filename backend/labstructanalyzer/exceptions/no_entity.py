import uuid


class EntityNotFoundException(Exception):
    """Исключение, возникающее при отсутствии сущности в БД"""

    def __init__(self, name: str, id: uuid.UUID):
        super().__init__(f"{name} с id {id} не найден")


class TemplateNotFoundException(EntityNotFoundException):
    """Исключение, возникающее при попытке доступа к несуществующему шаблону"""

    def __init__(self, template_id: uuid.UUID):
        super().__init__("Шаблон", template_id)


class ReportNotFoundException(EntityNotFoundException):
    """Исключение, возникающее при попытке доступа к несуществующему отчету"""

    def __init__(self, report_id: uuid.UUID):
        super().__init__("Отчет", report_id)
