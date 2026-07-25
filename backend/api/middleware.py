"""API middleware.

Configures logging, error handling, CORS,
and request timing middleware for the FastAPI application.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every incoming request and outgoing response."""

    async def dispatch(self, request, call_next):
        """Log request details and process the next handler."""
        pass
