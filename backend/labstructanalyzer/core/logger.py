import asyncio
import logging
import json
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Optional, Dict, Any

from labstructanalyzer.configs.config import BASE_PROJECT_DIR

LOG_DIR = os.path.join(BASE_PROJECT_DIR, 'logs')


class JsonLogFormatter(logging.Formatter):
    """
    Форматтер для преобразования записей журнала в JSON формат.
    Используется для вывода логов в файл
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Форматирует запись журнала в JSON строку

        Args:
            record: Запись журнала

        Returns:
            Строка в формате JSON
        """
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)


class ConsoleRequestFormatter(logging.Formatter):
    """
    Форматтер для вывода записей журнала в консоль,
    с дополнительной информацией о запросе (формат FastAPI)
    """
    _MAX_LEVEL_NAME_LENGTH = 8

    def format(self, record: logging.LogRecord) -> str:
        """
        Форматирует запись журнала для вывода в консоль

        Args:
            record: Запись журнала

        Returns:
            Отформатированная строка для вывода в консоль
        """
        message = record.getMessage()
        extra_lines = []

        if hasattr(record, 'extra_data'):
            extra_data: Dict[str, Any] = record.extra_data
            if 'request' in extra_data:
                request_info: Dict[str, str] = extra_data['request']
                method = request_info.get('method', '<нет метода>')
                url = request_info.get('url', '<нет url>')
                extra_lines.append(f'{method} request on {url}')
            if 'exception' in extra_data:
                extra_lines.append('error: ' + str(extra_data['exception']))

        level_name = record.levelname
        padded_level = f"{level_name}:".ljust(self._MAX_LEVEL_NAME_LENGTH + 1)
        formatted_message = f"{padded_level} {message}"

        if extra_lines:
            prefix = ' ' * (self._MAX_LEVEL_NAME_LENGTH + 1)
            formatted_message += "\n" + "\n".join(
                f"{prefix} {line}" for line in extra_lines
            )

        return formatted_message


class GlobalLogger:
    """
    Глобальный логгер, управляющий общей очередью и фоновой задачей.
    Использует паттерн Singleton для обеспечения единственного инстанса.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalLogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Инициализация глобального логгера
        """
        self._async_log_queue: asyncio.Queue[tuple[str, str, Optional[Any], Optional[Exception]]] = asyncio.Queue()
        self._async_log_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._logger_instances: Dict[str, Logger] = {}

    async def _extract_request_info(self, request: Any, level: str) -> Dict[str, Any]:
        """
        Извлекает и форматирует детали HTTP запроса

        Args:
            request: Объект запроса (например, из FastAPI)
            level: Уровень логирования для определения необходимости сохранения чувствительных данных

        Returns:
            Словарь с деталями запроса
        """
        try:
            body = await request.form()
            body_str = str({key: value for key, value in body.items()})
        except Exception as e:
            body_str = f"<ошибка чтения тела: {e}>"

        headers = dict(getattr(request, "headers", {}))
        filtered_headers = {}
        sensitive_headers = {"cookie", "authorization", "proxy-authorization"}
        for k, v in headers.items():
            if k.lower() not in sensitive_headers:
                filtered_headers[k] = v

        if level.upper() != "DEBUG":
            filtered_headers.pop('cookie', None)
        return {
            "url": str(getattr(request, "url", "<нет url>")),
            "method": getattr(request, "method", "<нет метода>"),
            "headers": filtered_headers,
            "body": body_str,
        }

    async def _log_request_details(self, logger: logging.Logger, level: str, message: str, request: Any,
                                   exc: Optional[Exception] = None):
        """
        Асинхронно логирует сообщение с деталями запроса

        Args:
            logger: Именованный логгер
            level: Уровень логирования
            message: Сообщение лога
            request: Объект запроса
            exc: Опциональное исключение
        """
        request_info = await self._extract_request_info(request, level)
        extra_data: Dict[str, Any] = {"request": request_info}
        if exc:
            extra_data["exception"] = str(exc)

        logger.log(getattr(logging, level.upper()), message, extra={"extra_data": extra_data})

    async def _async_log_worker(self):
        """
        Фоновая задача для обработки очереди асинхронных логов
        """
        while not self._shutdown_event.is_set():
            try:
                logger, level, message, request, exc = await asyncio.wait_for(self._async_log_queue.get(), timeout=1.0)
                await self._log_request_details(logger, level, message, request, exc)
                self._async_log_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                global_logger = logging.getLogger("global_logger")
                global_logger.error(f"Error in async log worker: {e}")

        while not self._async_log_queue.empty():
            logger, level, message, request, exc = self._async_log_queue.get_nowait()
            await self._log_request_details(logger, level, message, request, exc)
            self._async_log_queue.task_done()

    def _enqueue_async_log(self, logger: logging.Logger, level: str, message: str, request: Optional[Any] = None,
                           exc: Optional[Exception] = None):
        """
        Добавляет асинхронную задачу логирования в общую очередь

        Args:
            logger: Именованный логгер
            level: Уровень логирования
            message: Сообщение лога
            request: Опциональный объект запроса
            exc: Опциональное исключение
        """
        if not self._async_log_task or self._async_log_task.done():
            self._async_log_task = asyncio.create_task(self._async_log_worker())
        self._async_log_queue.put_nowait((logger, level, message, request, exc))

    async def shutdown(self):
        """
        Корректно завершает работу глобального логгера, обрабатывая оставшиеся элементы в очереди
        """
        global_logger = logging.getLogger("global_logger")
        global_logger.info("Shutting down global logger...")
        self._shutdown_event.set()
        if self._async_log_task:
            await self._async_log_queue.join()
            await self._async_log_task
        global_logger.info("Global logger shutdown complete.")

    def get_logger(self, name: str) -> 'Logger':
        """
        Возвращает именованный логгер. Если логгер с таким именем уже существует, возвращает его,
        иначе создает новый.

        Args:
            name: Имя логгера

        Returns:
            Объект Logger
        """
        if name not in self._logger_instances:
            self._logger_instances[name] = Logger(name, self)
        return self._logger_instances[name]


class Logger:
    """
    Класс для логирования событий приложения с поддержкой
    консольного вывода в читаемом формате и файлового вывода в JSON.
    Использует общую очередь из GlobalLogger.
    """

    def __init__(self, name: str, global_logger: GlobalLogger):
        """
        Инициализирует именованный логгер

        Args:
            name: Имя логгера
            global_logger: Глобальный логгер, управляющий общей очередью
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)

        json_formatter = JsonLogFormatter()
        console_formatter = ConsoleRequestFormatter()

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        self._logger.addHandler(console_handler)

        os.makedirs(LOG_DIR, exist_ok=True)

        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(LOG_DIR, 'lsa.log'),
            when='D',
            interval=1,
            backupCount=14,
        )
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(logging.WARNING)
        self._logger.addHandler(file_handler)

        self._global_logger = global_logger

    def debug(self, message: str, request: Optional[Any] = None, exc: Optional[Exception] = None):
        """
        Логирует сообщение с уровнем DEBUG

        Args:
            message: Сообщение лога
            request: Опциональный объект запроса
            exc: Опциональное исключение
        """
        self._log_with_optional_request(logging.DEBUG, message, request, exc)

    def info(self, message: str, request: Optional[Any] = None, exc: Optional[Exception] = None):
        """
        Логирует сообщение с уровнем INFO

        Args:
            message: Сообщение лога
            request: Опциональный объект запроса
            exc: Опциональное исключение
        """
        self._log_with_optional_request(logging.INFO, message, request, exc)

    def warning(self, message: str, request: Optional[Any] = None, exc: Optional[Exception] = None):
        """
        Логирует сообщение с уровнем WARNING.
        Может включать детали запроса и исключение (асинхронно)

        Args:
            message: Сообщение лога
            request: Опциональный объект запроса
            exc: Опциональное исключение
        """
        self._log_with_optional_request(logging.WARNING, message, request, exc)

    def error(self, message: str, request: Optional[Any] = None, exc: Optional[Exception] = None):
        """
        Логирует сообщение с уровнем ERROR.
        Может включать детали запроса и исключение (асинхронно)

        Args:
            message: Сообщение лога
            request: Опциональный объект запроса
            exc: Опциональное исключение
        """
        self._log_with_optional_request(logging.ERROR, message, request, exc)

    def critical(self, message: str, request: Optional[Any] = None, exc: Optional[Exception] = None):
        """
        Логирует сообщение с уровнем CRITICAL.
        Может включать детали запроса и исключение (асинхронно)

        Args:
            message: Сообщение лога
            request: Опциональный объект запроса
            exc: Опциональное исключение
        """
        self._log_with_optional_request(logging.CRITICAL, message, request, exc)

    def _log_with_optional_request(self, level: int, message: str, request: Optional[Any] = None,
                                   exc: Optional[Exception] = None):
        """
        Вспомогательная функция для логирования с опциональным запросом
        """
        extra_data: Dict[str, Any] = {}
        if exc:
            extra_data["exception"] = str(exc)
        if request:
            self._global_logger._enqueue_async_log(self._logger, logging.getLevelName(level), message, request, exc)
        else:
            self._logger.log(level, message, extra={"extra_data": extra_data})
