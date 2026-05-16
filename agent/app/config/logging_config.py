import logging
from logging import LogRecord

import colorlog
from asgi_correlation_id import CorrelationIdFilter

from app.config.settings import settings

log_format = (
    "%(log_color)s%(levelname)s%(reset)s "
    "%(blue)s%(asctime)s%(reset)s - "
    "%(purple)s%(correlation_id)s%(reset)s - "
    "%(cyan)s%(name)s%(reset)s - "
    "%(log_color)s%(message)s%(reset)s"
)

log_colors = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

color_formatter = colorlog.ColoredFormatter(log_format, log_colors=log_colors)
handler = logging.StreamHandler()
handler.addFilter(CorrelationIdFilter(uuid_length=32))


class CustomLogRecord(LogRecord):
    def getMessage(self):
        return str(self.msg)


class MultipleLogFormatter(logging.Formatter):
    _FORMATTERS: list[logging.Formatter] = []

    def add_formatter(self, formatter: logging.Formatter) -> None:
        self._FORMATTERS.append(formatter)

    def format(self, record: LogRecord) -> str:
        message = None
        if not self._FORMATTERS:
            return super().format(record)
        for formatter in self._FORMATTERS:
            message = formatter.format(record)
            record = CustomLogRecord(
                name=record.name,
                level=record.levelno,
                pathname=record.pathname,
                msg=message,
                exc_info=record.exc_info,
                func=record.funcName,
                args=record.args,
                sinfo=record.stack_info,
                lineno=record.lineno,
            )
        return message or ""


multi_formatter = MultipleLogFormatter()
multi_formatter.add_formatter(color_formatter)
handler.setFormatter(multi_formatter)

_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return

    level = logging.getLevelNamesMapping().get(settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, handlers=[handler], force=True)

    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False

    _configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    logger = colorlog.getLogger(name)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(logging.getLevelNamesMapping().get(settings.log_level.upper(), logging.INFO))
    logger.propagate = False
    return logger
