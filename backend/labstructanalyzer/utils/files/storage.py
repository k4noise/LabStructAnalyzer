from abc import ABC, abstractmethod
import uuid


class Storage(ABC):
    """
    Интерфейс для работы с файловыми хранилищами.
    Определяет базовые операции: сохранение, получение и удаление файлов
    """

    def generate_unique_name(self) -> str:
        """Генерация уникального имени файла на основе UUID"""
        return uuid.uuid4().hex

    @staticmethod
    @abstractmethod
    def can_init() -> bool:
        """
        Проверяет наличие необходимых параметров для инициализации хранилища

        Returns:
            True, если инициализация возможна
        """
        pass

    @abstractmethod
    def save(self, save_dir: str, file_data: bytes, extension: str) -> str | None:
        """
        Сохраняет данные в хранилище

        Args:
            save_dir: Директория/префикс для сохранения
            file_data: Данные файла в байтах
            extension: Расширение файла

        Returns:
            Ключ сохраненного файла или None в случае ошибки сохранения
        """
        pass

    @abstractmethod
    def get(self, file_path: str) -> bytes | None:
        """
        Получает данные из хранилища

        Args:
            file_path: Ключ к файлу

        Returns:
            Содержимое файла в байтах или None при отсутствии файла или возникновении ошибок
        """
        pass

    @abstractmethod
    def remove(self, file_path: str) -> bool:
        """
        Удаляет файл из хранилища

        Args:
            file_path: Ключ к файлу

        Returns:
            True, если файл был удален или его не существовало
        """
        pass
