import mimetypes
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from .storage import Storage


class S3Storage(Storage):
    """Реализация хранилища объектного типа S3"""
    REQUIRED_ENV_VARS = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_S3_BUCKET', 'AWS_S3_ENDPOINT_URL']

    def __init__(self):
        self.bucket_name = os.environ.get('AWS_S3_BUCKET')
        self.region_name = os.environ.get('AWS_DEFAULT_REGION', 'eu-north-1')
        self.endpoint_url = os.environ.get('AWS_S3_ENDPOINT_URL')

        from labstructanalyzer.main import global_logger
        self.logger = global_logger.get_logger(__name__)

        self._s3_client = None
        self._initialize()

    @staticmethod
    def can_init() -> bool:
        return all(key in os.environ for key in S3Storage.REQUIRED_ENV_VARS)

    def _initialize(self):
        """Инициализирует и проверяет S3 клиент"""
        if not self.can_init():
            self.logger.warning("Переменные окружения для S3 не сконфигурированы. S3Storage будет неактивен")
            return

        try:
            client_config = {
                'service_name': 's3',
                'aws_access_key_id': os.environ['AWS_ACCESS_KEY_ID'],
                'aws_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY'],
                'endpoint_url': self.endpoint_url,
                'region_name': self.region_name
            }

            self._s3_client = boto3.client(**client_config)
            self._s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"S3Storage успешно подключен к бакету '{self.bucket_name}'")

        except (NoCredentialsError, ClientError) as e:
            self._s3_client = None
            self.logger.error(f"Ошибка инициализации S3Storage: {e}")

    def save(self, save_dir: str, file_data: bytes, extension: str) -> str | None:
        if not self._s3_client:
            return None

        filename = f"{self.generate_unique_name()}{extension}"
        s3_key = self._normalize_key(os.path.join(save_dir, filename))
        content_type = mimetypes.guess_type(filename)
        try:
            self._s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type[0] if content_type else 'application/octet-stream'
            )
            self.logger.info(f"Файл успешно сохранен в S3: {s3_key}")
            return s3_key
        except ClientError as e:
            self.logger.error(f"Ошибка сохранения в S3: {e}")
            return None

    def get(self, file_path: str) -> bytes | None:
        if not self._s3_client:
            return None

        s3_key = self._normalize_key(file_path)

        try:
            response = self._s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            self.logger.info(f"Файл получен из S3: {s3_key}")
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.debug(f"Файл не найден в S3: {s3_key}")
            else:
                self.logger.error(f"Ошибка получения из S3: {e}")
            return None

    def remove(self, file_path: str) -> bool:
        if not self._s3_client:
            return False

        s3_key = self._normalize_key(file_path)

        try:
            self._s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            self.logger.info(f"Файл удален из S3: {s3_key}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.debug(f"Файл для удаления не найден в S3: {s3_key}")
                return True
            else:
                self.logger.error(f"Ошибка удаления из S3: {e}")
                return False

    def _normalize_key(self, path: str) -> str:
        """Нормализует путь для S3 (заменяет обратные слеши)"""
        return path.replace("\\", "/")
