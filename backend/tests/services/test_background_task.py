import sys
import types
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

_mock_logger = MagicMock()
_module_stub = types.ModuleType("labstructanalyzer.core.logger")
_module_stub.GlobalLogger = MagicMock(return_value=MagicMock(get_logger=lambda *_: _mock_logger))
sys.modules["labstructanalyzer.core.logger"] = _module_stub


def create_async_session_mock() -> MagicMock:
    session = MagicMock()
    session.add_all = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


from labstructanalyzer.services.background_task import BackgroundTaskService


class BackgroundTaskServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db_session = create_async_session_mock()
        self.mock_redis = MagicMock()
        self.mock_queue = MagicMock()
        self.mock_job = MagicMock(id="job123", is_finished=False, is_failed=False, get_status=lambda: "queued")
        self.mock_queue.enqueue = MagicMock(return_value=self.mock_job)

        with patch("labstructanalyzer.services.background_task.Queue", return_value=self.mock_queue):
            self.service = BackgroundTaskService(self.db_session, self.mock_redis)

        _mock_logger.reset_mock()

    def test_enqueue_adds_job_to_queue_and_logs(self):
        """enqueue должен добавлять задачу в очередь и логировать сообщение"""
        fn = MagicMock()
        job = self.service.enqueue(fn, 42, test="ok")

        self.mock_queue.enqueue.assert_called_once()
        called_args, called_kwargs = self.mock_queue.enqueue.call_args

        self.assertEqual(called_args[0], fn)
        self.assertEqual(called_args[1], 42)
        self.assertEqual(called_kwargs["test"], "ok")

        self.assertIn("retry", called_kwargs)
        self.assertIn("failure_ttl", called_kwargs)

        self.assertEqual(job, self.mock_job)
        _mock_logger.info.assert_called_once()
        self.assertIn("Задача job123 добавлена в очередь", _mock_logger.info.call_args[0][0])

    async def test_save_changes_successful(self):
        """Должен сохранять изменения и коммитить транзакцию"""
        data = [{"id": 1}]
        await self.service.save_changes(data)
        self.db_session.add_all.assert_called_once_with(data)
        self.db_session.commit.assert_awaited_once()
        _mock_logger.info.assert_any_call("Данные успешно сохранены в базе данных")

    async def test_save_changes_with_none(self):
        """Не должен ничего делать, если None"""
        await self.service.save_changes(None)
        self.db_session.add_all.assert_not_called()
        self.db_session.commit.assert_not_awaited()

    async def test_save_changes_rollback_on_error(self):
        """При ошибке commit должен сделать rollback"""
        self.db_session.add_all.side_effect = Exception("DB error")
        with self.assertRaises(Exception):
            await self.service.save_changes([{"x": 1}])
        self.db_session.rollback.assert_awaited_once()
        _mock_logger.error.assert_called_once()

    async def test_handle_task_result_saves_dict_result(self):
        """handle_task_result должен нормализовывать dict и сохранять"""
        with patch.object(self.service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.service.handle_task_result({"key": "val"})
        mock_save.assert_awaited_once_with([{"key": "val"}])

    async def test_handle_task_result_saves_list_result(self):
        """handle_task_result должен сохранять list as-is"""
        items = [{"a": 1}]
        with patch.object(self.service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.service.handle_task_result(items)
        mock_save.assert_awaited_once_with(items)

    async def test_handle_task_result_none(self):
        """handle_task_result с None не должен вызывать save_changes"""
        with patch.object(self.service, "save_changes", new_callable=AsyncMock) as mock_save:
            await self.service.handle_task_result(None)
        mock_save.assert_not_awaited()

    async def test_handle_task_result_error_rollbacks(self):
        """При ошибке в save_changes должен делать rollback и логировать"""
        with patch.object(self.service, "save_changes", new_callable=AsyncMock) as mock_save:
            mock_save.side_effect = Exception("Test")
            await self.service.handle_task_result([{"a": 1}])
        self.db_session.rollback.assert_awaited_once()
        _mock_logger.error.assert_called_once()
        self.assertIn("Ошибка при обработке результата задачи", _mock_logger.error.call_args[0][0])

    def test_normalize_result_list_passthrough(self):
        sample = [{"id": 1}]
        self.assertEqual(self.service._normalize_result(sample), sample)

    def test_normalize_result_dict_wrapped(self):
        sample = {"a": 1}
        self.assertEqual(self.service._normalize_result(sample), [sample])

    def test_normalize_result_iterable(self):
        class Gen:
            def __iter__(self): yield {"i": 1}

        result = self.service._normalize_result(Gen())
        self.assertEqual(result, [{"i": 1}])

    def test_normalize_result_invalid_type(self):
        result = self.service._normalize_result(123)
        self.assertIsNone(result)
        _mock_logger.warning.assert_called_once()

    def test_get_job_status_returns_valid_status(self):
        with patch("labstructanalyzer.services.background_task.Job.fetch", return_value=self.mock_job):
            status = self.service.get_job_status("job123")

        self.assertEqual(status["status"], "queued")
        self.assertIsNone(status["result"])
        self.assertIsNone(status["exc_info"])

    def test_get_job_status_not_found(self):
        with patch("labstructanalyzer.services.background_task.Job.fetch", return_value=None):
            status = self.service.get_job_status("not_found")
        self.assertEqual(status, {"status": "not_found"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
