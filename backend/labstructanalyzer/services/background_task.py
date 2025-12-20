from typing import Any, Callable, Dict, Optional, Union
from redis import Redis
from rq import Queue
from rq.job import Job, Retry

from labstructanalyzer.core.logger import GlobalLogger


class BackgroundTaskService:
    """Сервис для управления фоновыми задачами через RQ"""

    DEFAULT_RETRY_MAX = 3
    DEFAULT_RETRY_INTERVALS = [30, 60, 120]  # секунды
    DEFAULT_FAILURE_TTL = 24 * 3600  # 24 часа
    DEFAULT_TIMEOUT = 600  # 10 минут

    def __init__(self, redis_conn: Redis, queue_name: str = 'default'):
        self.logger = GlobalLogger().get_logger(__name__)
        self.redis_conn = redis_conn
        self.queue = Queue(name=queue_name, connection=redis_conn)

    def enqueue(self, fn: Callable, *args: Any, **kwargs: Any) -> Optional[Job]:
        """Добавляет задачу в очередь RQ. Вернет Job объект или None при ошибке"""
        try:
            retry = Retry(
                max=self.DEFAULT_RETRY_MAX,
                interval=self.DEFAULT_RETRY_INTERVALS
            )

            job = self.queue.enqueue(
                fn,
                *args,
                retry=retry,
                timeout=self.DEFAULT_TIMEOUT,
                failure_ttl=self.DEFAULT_FAILURE_TTL,
                **kwargs
            )

            self.logger.info(f"Задача {job.id} добавлена в очередь")
            return job

        except Exception as e:
            self.logger.error(f"Ошибка при добавлении задачи в очередь: ", exc=e)
            return None

    def get_job_status(self, job_id: str) -> Dict[str, Union[str, Any]]:
        """Возвращает статус задачи по её ID"""
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
        except Exception:
            return {"status": "not_found"}

        if job is None:
            return {"status": "not_found"}

        return {
            "status": job.get_status(),
            "result": job.return_value() if job.is_finished else None,
            "exc_info": job.latest_result() if job.is_failed else None
        }
