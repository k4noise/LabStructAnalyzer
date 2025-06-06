from .storage import Storage
from .local import LocalStorage
from .s3 import S3Storage


class ChainStorage:
    """
    Общий класс для хранилищ, который пытается выполнить операции на каждом хранилище по порядку,
    пока одна из операций не увенчается успехом.
    Обход хранилищ осуществляется последовательно с первого переданного
    """
    DEFAULT_STORAGES = [S3Storage, LocalStorage]

    def __init__(self, *storages: Storage):
        if not storages:
            raise ValueError("Укажите минимум одно хранилище")

        self.storages = storages
        storage_names = ', '.join(type(storage).__name__ for storage in self.storages)

        from labstructanalyzer.main import global_logger
        self.logger = global_logger.get_logger(__name__)
        self.logger.debug(f"Инициализирована цепочка хранилищ: [{storage_names}]")

    @classmethod
    def get_default(cls):
        """
        Создает экземпляр ChainStorage с автоматически сконфигурированными хранилищами.
        Проверяет доступность каждого хранилища из DEFAULT_STORAGES
        и включает в цепочку только те, которые могут быть инициализированы

        Returns:
            Экземпляр ChainStorage с цепочкой из доступных хранилищ
        """
        storages = [Candidate() for Candidate in cls.DEFAULT_STORAGES if Candidate.can_init()]
        return cls(*storages)

    def save(self, save_dir: str, file_data: bytes, extension: str) -> str:
        """
        Пытается сохранить файл, проходя по цепочке хранилищ

        Args:
            save_dir: Директория/префикс для сохранения
            file_data: Данные файла в байтах
            extension: Расширение файла

        Returns:
            Ключ сохраненного файла от первого успешно сработавшего хранилища

        Raises:
            IOError: Если не удалось сохранить файл ни в одном из хранилищ
        """
        for storage in self.storages:
            path = storage.save(save_dir, file_data, extension)
            if path:
                return path

        raise IOError("Не удалось сохранить файл ни в одном из хранилищ в цепочке")

    def get(self, file_path: str) -> bytes | None:
        """
        Пытается найти и получить файл, проходя по цепочке хранилищ

        Args:
            file_path: Ключ к файлу

        Returns:
            Содержимое файла в байтах от первого хранилища, где файл был найден,
            или None при отсутствии файла во всех хранилищах
        """
        for storage in self.storages:
            data = storage.get(file_path)
            if data is not None:
                return data

        self.logger.warning(f"Файл '{file_path}' не найден ни в одном из хранилищ")
        return None

    def remove(self, file_path: str) -> bool:
        """
        Проходит по всем хранилищам и удаляет файл

        Args:
            file_path: Ключ к файлу

        Returns:
            True, если файл был успешно хотя бы в одном из хранилищ
        """
        any_deleted = False
        for storage in self.storages:
            if storage.remove(file_path):
                any_deleted = True
        return any_deleted
