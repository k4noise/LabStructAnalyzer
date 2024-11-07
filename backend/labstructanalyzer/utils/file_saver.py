import os
import uuid

BASE_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FileSaver:
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
        file_name = f"{FileSaver.generate_unique_name()}{extension}"
        try:
            file_path = os.path.join(BASE_PROJECT_DIR, save_dir, file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            # with open(file_path, "wb") as file:
            #     file.write(file_data)
            return os.path.join(save_dir, file_name)
        except IOError as error:
            print(f"Произошла ошибка при сохранении файла {file_name}: {error}")

    @staticmethod
    def generate_unique_name() -> str:
        """Генерирует уникальное имя файла с помощью UUID

        Returns:
            Уникальное имя файла
        """
        return uuid.uuid4().hex
