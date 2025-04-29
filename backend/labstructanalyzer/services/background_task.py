from sqlalchemy.ext.asyncio import AsyncSession
from concurrent.futures import Future
import asyncio
from typing import List

from labstructanalyzer.main import global_logger

logger = global_logger.get_logger(__name__)


class BackgroundTaskService:
    """Сервис для обработки результатов фоновых задач и сохранения их в БД"""

    def __init__(self, db_session: AsyncSession):
        """Инициализирует сервис BackgroundTaskService

        Args:
            db_session: Асинхронная сессия SQLAlchemy для работы с БД.
        """
        self.db_session = db_session

    async def save_changes(self, changed_items: List[dict]):
        """Асинхронно сохраняет список измененных объектов в базе данных"""
        try:
            self.db_session.add_all(changed_items)
            await self.db_session.commit()
            logger.info("Предварительные оценки успешно сохранены в базе данных")
        except Exception as exception:
            await self.db_session.rollback()
            logger.error("Ошибка при сохранении предварительных оценок в базу данных", None, exception)

    async def handle_task_result(self, future: Future):
        """Асинхронно обрабатывает результат завершенной фоновой задачи (Future)"""
        try:
            result = await asyncio.wrap_future(future)
            await self.save_changes(result)
        except Exception as exception:
            logger.error(f"Ошибка при обработке результата", None, exception)
