"""API middleware.

Configures logging, error handling, CORS,
and request timing middleware for the FastAPI application.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs the processing time of each request."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = time.perf_counter() - start
        logger.info(
            "%s %s -> %d (%.4fs)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response
