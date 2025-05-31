import os
from pathlib import Path
from .storage import Storage
from labstructanalyzer.configs.config import BASE_PROJECT_DIR
from labstructanalyzer.main import global_logger

logger = global_logger.get_logger(__name__)


class LocalStorage(Storage):
    """Реализация хранилища с использованием локальной файловой системы"""

    def __init__(self, base_path: str = BASE_PROJECT_DIR):
        self.base_path = Path(base_path)
        if not self.base_path.is_dir():
            logger.warning(f"Базовая директория для LocalStorage не существует: {self.base_path}")

    @staticmethod
    def can_init() -> bool:
        base_path = Path(BASE_PROJECT_DIR)
        return base_path.exists() and os.access(base_path, os.W_OK)

    def save(self, save_dir: str, file_data: bytes, extension: str) -> str | None:
        filename = f"{self.generate_unique_name()}{extension}"
        relative_path = os.path.join(save_dir, filename)
        full_path = self._get_full_path(relative_path)

        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(file_data)
            logger.info(f"Файл сохранен локально: {full_path}")
            return relative_path
        except IOError as e:
            logger.error(f"Ошибка сохранения локального файла {full_path}: {e}")
            return None

    def get(self, file_path: str) -> bytes | None:
        full_path = self._get_full_path(file_path)

        if not full_path.exists():
            logger.debug(f"Локальный файл не найден: {full_path}")
            return None

        try:
            data = full_path.read_bytes()
            logger.info(f"Файл получен локально: {full_path}")
            return data
        except IOError as e:
            logger.error(f"Ошибка чтения локального файла {full_path}: {e}")
            return None

    def remove(self, file_path: str) -> bool:
        full_path = self._get_full_path(file_path)

        if not full_path.exists():
            logger.debug(f"Файл для удаления не существует: {full_path}")
            return True

        try:
            full_path.unlink()
            logger.info(f"Файл удален локально: {full_path}")

            return True
        except OSError as e:
            logger.error(f"Ошибка удаления локального файла {full_path}: {e}")
            return False

    def _get_full_path(self, relative_path: str) -> Path:
        """Преобразует относительный путь в полный"""
        return self.base_path / relative_path
