from sqlalchemy.ext.asyncio import AsyncSession
from concurrent.futures import Future
import asyncio
from typing import List, Any, Optional
from labstructanalyzer.main import global_logger

logger = global_logger.get_logger(__name__)


class BackgroundTaskService:
    """Сервис для обработки результатов фоновых задач и сохранения их в БД"""

    def __init__(self, db_session: AsyncSession):
        """Инициализирует сервис BackgroundTaskService"""
        self.db_session = db_session

    async def save_changes(self, changed_items: Optional[List[dict]]):
        """Асинхронно сохраняет список измененных объектов в базе данных."""
        if changed_items is None:
            return  # Не вызываем add_all, если данные отсутствуют

        try:
            self.db_session.add_all(changed_items)
            await self.db_session.commit()
            logger.info("Данные успешно сохранены в базе данных")
        except Exception as exception:
            await self.db_session.rollback()
            logger.error("Ошибка при сохранении данных в базу данных", exc_info=exception)
            raise

    async def handle_task_result(self, future: Future):
        """Асинхронно обрабатывает результат завершенной фоновой задачи."""

        try:
            result = await asyncio.wrap_future(future)
            normalized_result = self._normalize_result(result)

            if normalized_result is not None:
                await self.save_changes(normalized_result)

        except Exception as exception:
            await self.db_session.rollback()
            logger.error("Ошибка при обработке результата задачи", exc=exception)

    def _normalize_result(self, result: Any) -> Optional[List[dict]]:
        """Нормализует результат задачи в список словарей для сохранения."""
        if result is None:
            return None  # Возвращаем None вместо пустого списка

        if isinstance(result, list):
            return result

        if isinstance(result, dict):
            return [result]

        try:
            return list(result)
        except (TypeError, ValueError):
            logger.warning(f"Невозможно нормализовать результат типа {type(result).__name__}")
            return None
