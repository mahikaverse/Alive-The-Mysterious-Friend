"""Logging configuration.

Sets up structured logging for the application
using Python's built-in logging module.
"""

import logging
import sys

from backend.config.settings import settings
from backend.utils.logging_context import RequestIDFilter


def setup_logging() -> None:
    """Configure root logger with structured format and appropriate level."""
    level = logging.DEBUG if settings.debug else getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
