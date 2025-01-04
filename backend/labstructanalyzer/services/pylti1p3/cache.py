from pylti1p3.launch_data_storage.cache import CacheDataStorage


class FastAPICacheDataStorage(CacheDataStorage):
    """
    Сервис для кеширования запросов
    """
    _cache = None

    def __init__(self, cache, **kwargs):
        self._cache = cache
        super().__init__(cache, **kwargs)