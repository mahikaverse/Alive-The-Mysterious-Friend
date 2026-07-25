"""Logger utility.

Provides a factory function to create consistent
loggers for every module in the application.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance with the given name."""
    return logging.getLogger(name)
