import redis
import pickle
import logging
import threading


class RedisCache:
    """Синхронный потокобезопасный кеш с вытеснением старых записей на основе Redis"""

    def __init__(self, host='localhost', port=6379, db=0):
        self._redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=False,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        self._logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            try:
                value = self._redis.get(key)
                if value is None:
                    return None
                return pickle.loads(value)
            except redis.RedisError as e:
                self._logger.error(f"Ошибка при получении ключа {key}: {e}")
                return None

    def set(self, key, value, ttl):
        with self._lock:
            try:
                self._redis.set(key, pickle.dumps(value), ex=ttl)
            except redis.RedisError as e:
                self._logger.error(f"Ошибка при установке ключа {key}: {e}")

    def delete(self, key):
        with self._lock:
            try:
                self._redis.delete(key)
            except redis.RedisError as e:
                self._logger.error(f"Ошибка при удалении ключа {key}: {e}")

    def clear(self):
        with self._lock:
            try:
                self._redis.flushdb()
            except redis.RedisError as e:
                self._logger.error(f"Ошибка при очистке кеша: {e}")

    def get_cache_size(self):
        with self._lock:
            try:
                return self._redis.dbsize()
            except redis.RedisError as e:
                self._logger.error(f"Ошибка при получении размера кеша: {e}")
                return 0

    def get_connection(self):
        return self._redis
