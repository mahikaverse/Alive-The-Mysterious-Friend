"""Context-aware logging filter.

Attaches the current request_id from contextvars to every
log record so structured logs can include it.
"""

import logging

from backend.utils.request_context import get_current_request_id


class RequestIDFilter(logging.Filter):
    """Log filter that injects the active request_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_current_request_id() or "-"
        return True
