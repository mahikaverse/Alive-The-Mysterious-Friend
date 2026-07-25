"""Logging configuration.

Sets up structured logging for the application
using Python's built-in logging module.
"""

import logging
import sys


def setup_logging() -> None:
    """Configure root logger with structured format and appropriate level."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
