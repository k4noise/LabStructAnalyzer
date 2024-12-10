import time
import threading


class TTLCache:
    def __init__(self):
        self._cache = {}
        self._lock = threading.RLock()

    def get(self, key):
        with self._lock:
            if key in self._cache:
                value, timestamp, ttl = self._cache[key]
                if time.time() - timestamp <= ttl:
                    return value
                else:
                    self.delete(key)
            return None

    def set(self, key, value, ttl):
        with self._lock:
            self._cache[key] = (value, time.time(), ttl)

    def delete(self, key):
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        with self._lock:
            self._cache.clear()

    def get_cache_size(self):
        with self._lock:
            return len(self._cache)
