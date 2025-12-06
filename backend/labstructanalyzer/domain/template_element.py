import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class TemplateElementPropsUpdate:
    """Пара id-свойства для обновления существующего элемента"""
    element_id: uuid.UUID
    properties: Dict[str, Any]


@dataclass(frozen=True)
class PlainTemplateElement:
    """
    Представление элемента после нормализации вложенной структуры,
    сохраняющее связь с родительским элементом
    """
    type: str
    order: int
    parent_element_id: Optional[uuid.UUID] = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    properties: Dict[str, Any] = field(default_factory=dict)
