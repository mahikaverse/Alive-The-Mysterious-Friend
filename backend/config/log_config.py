"""Logging configuration.

Sets up structured logging for the application
using Python's built-in logging module.

In development: human-readable coloured format.
In production: JSON format for log aggregation.
"""

import json
import logging
import sys

from backend.config.settings import settings
from backend.utils.logging_context import RequestIDFilter


class JSONFormatter(logging.Formatter):
    """Outputs log records as JSON lines for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "request_id": getattr(record, "request_id", "-"),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging() -> None:
    """Configure root logger with format appropriate for the current environment."""
    level = logging.DEBUG if settings.debug else getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if settings.is_production:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
