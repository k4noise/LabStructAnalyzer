import sys
import types
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

_mock_logger = MagicMock()
_module_stub = types.ModuleType("labstructanalyzer.core.logger")
_module_stub.GlobalLogger = MagicMock(return_value=MagicMock(get_logger=lambda *_: _mock_logger))
sys.modules["labstructanalyzer.core.logger"] = _module_stub


def create_async_session_mock() -> MagicMock:
    """Создает мок-объект, имитирующий асинхронную сессию SQLModel"""
    session = MagicMock()
    session.add_all = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


from labstructanalyzer.services.background_task import BackgroundTaskService


class BackgroundTaskServiceTests(unittest.IsolatedAsyncioTestCase):
    """Тесты для сервиса обработки фоновых задач"""

    def setUp(self) -> None:
        self.db_session = create_async_session_mock()
        self.task_service = BackgroundTaskService(self.db_session)
        _mock_logger.reset_mock()  # Сброс мок-логгера перед каждым тестом

    async def test_submit_creates_background_task(self):
        """Проверка, что submit создает фоновую задачу"""
        mock_fn = AsyncMock(return_value="result")

        async def wrapped_fn():
            return await mock_fn()

        await self.task_service.submit(wrapped_fn)

        # Проверяем, что задача была создана
        self.assertTrue(any(
            task.coro.cr_code.co_name == 'handle_task_result'  # Исправлено здесь
            for task in asyncio.all_tasks()
        ))

    async def test_concurrent_task_processing(self):
        """Проверка корректной параллельной обработки нескольких задач"""
        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            futures = []
            for i in range(3):
                async def task(i=i):
                    return [{"record_id": i, "value": f"test_{i}"}]

                future = asyncio.create_task(task())
                futures.append(future)

            await asyncio.gather(*futures)

            self.assertEqual(mock_save.call_count, 3)

            for i in range(3):
                args, _ = mock_save.call_args_list[i]
                self.assertEqual(args[0], [{"record_id": i, "value": f"test_{i}"}])

    async def test_successful_task_processing(self):
        """Проверка корректной обработки успешного результата"""
        test_data = [{"id": 1, "status": "completed"}]

        async def successful_task():
            return test_data

        future = asyncio.create_task(successful_task())

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.task_service.handle_task_result(future)
            mock_save.assert_awaited_once_with(test_data)

    async def test_error_handling_absorbs_exceptions(self):
        """Проверка, что обработчик поглощает исключения"""
        future = asyncio.Future()
        future.set_exception(RuntimeError("Test exception"))

        await self.task_service.handle_task_result(future)

        _mock_logger.error.assert_called_once()
        self.assertIn("Ошибка при обработке результата задачи", _mock_logger.error.call_args[0][0])

    async def test_rollback_on_task_error(self):
        """Проверка отката транзакции при ошибке в задаче"""
        future = asyncio.Future()
        future.set_exception(ValueError("Database constraint violation"))

        await self.task_service.handle_task_result(future)

        self.db_session.rollback.assert_awaited_once()

    async def test_null_result_handling(self):
        """Проверка обработки None-результата"""
        future = asyncio.Future()
        future.set_result(None)

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.task_service.handle_task_result(future)
            mock_save.assert_not_called()

    async def test_empty_result_handling(self):
        """Проверка обработки пустого списка"""
        future = asyncio.Future()
        future.set_result([])

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.task_service.handle_task_result(future)
            mock_save.assert_awaited_once_with([])

    async def test_successful_data_saving(self):
        """Проверка успешного сохранения данных"""
        records = [{"id": 1, "name": "Test Record"}]
        await self.task_service.save_changes(records)

        self.db_session.add_all.assert_called_once_with(records)
        self.db_session.commit.assert_awaited_once()
        _mock_logger.info.assert_called_once_with("Данные успешно сохранены в базе данных")

    async def test_rollback_on_commit_failure(self):
        """Проверка отката при ошибке commit"""
        self.db_session.commit.side_effect = Exception("Database connection lost")

        with self.assertRaises(Exception):
            await self.task_service.save_changes([{"id": 1}])

        self.db_session.rollback.assert_awaited_once()
        _mock_logger.error.assert_called_once()

    async def test_empty_list_saving(self):
        """Проверка сохранения пустого списка"""
        await self.task_service.save_changes([])

        self.db_session.add_all.assert_called_once_with([])
        self.db_session.commit.assert_awaited_once()

    async def test_invalid_data_handling(self):
        """Проверка обработки некорректных данных"""
        invalid_records = [None, "not_a_dict", 123]

        self.db_session.add_all.side_effect = TypeError("Expected dictionary objects")

        with self.assertRaises(TypeError):
            await self.task_service.save_changes(invalid_records)

        self.db_session.rollback.assert_awaited_once()
        _mock_logger.error.assert_called_once()

    async def test_non_list_result_normalization(self):
        """Проверка нормализации неспискового результата"""
        future = asyncio.Future()
        future.set_result({"single_record": True})

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.task_service.handle_task_result(future)
            mock_save.assert_awaited_once_with([{"single_record": True}])

    async def test_rollback_on_save_error(self):
        """Проверка отката при ошибке сохранения"""
        future = asyncio.Future()
        future.set_result([{"id": 1}])

        with patch.object(self.task_service, "save_changes", new_callable=AsyncMock) as mock_save:
            mock_save.side_effect = Exception("Error during save operation")
            await self.task_service.handle_task_result(future)

            _mock_logger.error.assert_called_once()
            self.db_session.rollback.assert_awaited_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
