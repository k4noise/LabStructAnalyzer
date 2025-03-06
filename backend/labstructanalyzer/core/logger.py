import asyncio
import logging
from typing import Optional


class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

        # TODO ВНИМАНИЕ ХАРДКОД
        file_handler = logging.FileHandler('app.log')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.WARNING)
        self.logger.addHandler(file_handler)

    def _format_request_details(self, request) -> str:
        try:
            body = request.json()
            body_str = body.decode('utf-8') if isinstance(body, bytes) else "<no body>"
        except Exception as e:
            body_str = f"<error reading body: {e}>"

        return (
            f"\nRequest URL: {getattr(request, 'url', '<no url>')}"
            f"\nMethod: {getattr(request, 'method', '<no method>')}"
            f"\nHeaders: {dict(getattr(request, 'headers', {}))}"
            f"\nBody: {body_str}"
        )

    def _log(self, level: str, message: str, request=None, exc: Optional[Exception] = None):
        if request:
            message += self._format_request_details(request)
        log_method = getattr(self.logger, level)
        log_method(message, exc_info=exc is not None)

    def debug(self, message: str):
        self._log("debug", message)

    def info(self, message: str):
        self._log("info", message)

    def warning(self, message: str, request=None, exc: Optional[Exception] = None):
        self._log("warning", message, request, exc)

    def error(self, message: str, request=None, exc: Optional[Exception] = None):
        self._log("error", message, request, exc)

    def critical(self, message: str, request=None, exc: Optional[Exception] = None):
        self._log("critical", message, request, exc)
