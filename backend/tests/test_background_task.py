import sys
import types
import asyncio
import random
import unittest
import importlib
from asyncio import Future
from unittest.mock import MagicMock, AsyncMock, patch

_mock_logger = MagicMock()
_module_stub = types.ModuleType("labstructanalyzer.main")
_module_stub.global_logger = types.SimpleNamespace(get_logger=lambda *_: _mock_logger)
sys.modules["labstructanalyzer.main"] = _module_stub

bg_module = importlib.import_module("labstructanalyzer.services.background_task")
BackgroundTaskService = bg_module.BackgroundTaskService  # type: ignore


def create_async_session_mock() -> MagicMock:
    """Создает мок-объект, имитирующий асинхронную сессию SQLModel"""
    session = MagicMock()
    session.add_all = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


class BackgroundTaskServiceTests(unittest.IsolatedAsyncioTestCase):
    """Тесты для сервиса обработки фоновых задач"""

    def setUp(self) -> None:
        self.db_session = create_async_session_mock()
        self.task_service = BackgroundTaskService(self.db_session)
        _mock_logger.reset_mock()

    async def test_task_without_retry_fails(self):
        """Задача без механизма повторных попыток должна завершаться с ошибкой"""

        def failing_function(_: int) -> int:
            raise RuntimeError("Simulated error")

        future = asyncio.get_running_loop().run_in_executor(None, failing_function, 1)
        with self.assertRaises(RuntimeError):
            await future

    async def test_flaky_tasks_without_handling_fail(self):
        """
        Нестабильные задачи без обработки ошибок должны приводить к сбоям
        """

        def flaky_function(idx: int, failure_rate: float = 1.0) -> int:
            if random.random() < failure_rate:
                raise RuntimeError(f"Random failure #{idx}")
            return idx

        tasks = [
            asyncio.get_running_loop().run_in_executor(None, flaky_function, i)
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.assertEqual(sum(isinstance(r, Exception) for r in results), 5)

    async def test_error_handling_absorbs_exceptions(self):
        """Проверка, что обработчик задач корректно поглощает исключения"""
        future = Future()
        future.set_exception(RuntimeError("Test exception"))

        await self.task_service.handle_task_result(future)

        _mock_logger.error.assert_called_once()

    async def test_rollback_on_task_error(self):
        """При возникновении ошибки в задаче должен выполняться откат транзакции"""
        future = Future()
        future.set_exception(ValueError("Database constraint violation"))

        await self.task_service.handle_task_result(future)

        self.db_session.rollback.assert_awaited_once()

    async def test_null_result_handling(self):
        """Проверка корректной обработки None-результата задачи"""
        future = Future()
        future.set_result(None)

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.task_service.handle_task_result(future)
            mock_save.assert_not_called()

    async def test_empty_result_handling(self):
        """Проверка корректной обработки пустого списка результатов"""
        future = Future()
        future.set_result([])

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.task_service.handle_task_result(future)
            mock_save.assert_awaited_once_with([])

    async def test_concurrent_task_processing(self):
        """Проверка корректной параллельной обработки нескольких задач"""
        futures = []
        for i in range(3):
            future = Future()
            future.set_result([{"record_id": i, "value": f"test_{i}"}])
            futures.append(future)

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            await asyncio.gather(*(self.task_service.handle_task_result(f) for f in futures))
            self.assertEqual(mock_save.call_count, 3)

    async def test_successful_data_saving(self):
        """Проверка успешного сохранения данных в базу при отсутствии ошибок"""
        records = [{"id": 1, "name": "Test Record"}]
        await self.task_service.save_changes(records)

        self.db_session.add_all.assert_called_once_with(records)
        self.db_session.commit.assert_awaited_once()
        self.db_session.rollback.assert_not_awaited()

        _mock_logger.info.assert_called_once()
        _mock_logger.error.assert_not_called()

    async def test_rollback_on_commit_failure(self):
        """При ошибке во время commit должен выполняться rollback и логироваться ошибка"""
        self.db_session.commit.side_effect = Exception("Database connection lost")
        with self.assertRaises(Exception):
            await self.task_service.save_changes([{"id": 1}])

        self.db_session.rollback.assert_awaited_once()
        _mock_logger.error.assert_called_once()

    async def test_empty_list_saving(self):
        """Проверка корректной обработки сохранения пустого списка записей"""
        await self.task_service.save_changes([])

        self.db_session.add_all.assert_called_once_with([])
        self.db_session.commit.assert_awaited_once()

    async def test_invalid_data_handling(self):
        """Проверка корректной обработки некорректных данных при сохранении"""
        invalid_records = [None, "not_a_dict", 123]

        self.db_session.add_all.side_effect = TypeError("Expected dictionary objects")

        with self.assertRaises(TypeError):
            await self.task_service.save_changes(invalid_records)

        self.db_session.rollback.assert_awaited_once()
        _mock_logger.error.assert_called_once()

    async def test_successful_task_result_processing(self):
        """Проверка корректной обработки успешного результата задачи"""
        records = [{"id": 1, "status": "completed"}]
        future = Future()
        future.set_result(records)

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.task_service.handle_task_result(future)
            mock_save.assert_awaited_once_with(records)

    async def test_non_list_result_normalization(self):
        """Проверка нормализации результата, который не является списком"""
        future = Future()
        future.set_result({"single_record": True})

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.task_service.handle_task_result(future)
            mock_save.assert_awaited_once_with([{"single_record": True}])

    async def test_rollback_on_save_error(self):
        """Проверка выполнения отката транзакции при ошибке в процессе сохранения"""
        future = Future()
        future.set_result([{"id": 1}])

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            mock_save.side_effect = Exception("Error during save operation")
            await self.task_service.handle_task_result(future)

            _mock_logger.error.assert_called_once()
            self.db_session.rollback.assert_awaited_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
