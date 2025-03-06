import os
import uuid

class FileUtils:
    BASE_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def save(save_dir: str, file_data: bytes, extension: str) -> str:
        """Сохраняет сырые данные файла с уникальным именем в указанную папку

        Args:
          extension: Расширение файла
          save_dir: Папка для сохранения
          file_data: Данные файла

        Returns:
          Относительный путь до сохраненного файла
        """
        file_name = f"{FileUtils.generate_unique_name()}{extension}"
        file_path = os.path.join(FileUtils.BASE_PROJECT_DIR, save_dir, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as file:
            file.write(file_data)
        return os.path.join(save_dir, file_name)

    @staticmethod
    def generate_unique_name() -> str:
        """Генерирует уникальное имя файла с помощью UUID

        Returns:
            Уникальное имя файла
        """
        return uuid.uuid4().hex

    @staticmethod
    def get(folder: str, filename: str):
        """
        Получить файл с указанным именем из указанной папки

        Returns:
            Прочитанный файл в бинарном режиме

        Raises:
            IOError Файл не найден
        """
        file_path = os.path.join(FileUtils.BASE_PROJECT_DIR, folder, filename)

        with open(file_path, 'rb') as file:
            return file.read()

    @staticmethod
    def remove(folder: str, filename: str):
        """
        Удалить файл

        Raises:
            IOError Файл не найден
        """
        if filename.startswith('/'):
            filename = filename[1:]
        file_path = os.path.join(FileUtils.BASE_PROJECT_DIR, folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            raise IOError("Файл не найден")
