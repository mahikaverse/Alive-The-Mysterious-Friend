"""API middleware.

Configures request context, timing, and CORS
for the FastAPI application.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.utils.request_context import generate_request_id, set_request_id, reset_request_id

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Generates a unique request_id per request and attaches it to
    request.state and the response headers for traceability."""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID", generate_request_id())

        request.state.request_id = rid
        request.state.start_time = time.perf_counter()

        token = set_request_id(rid)
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            elapsed = time.perf_counter() - request.state.start_time
            logger.info(
                "[%s] %s %s -> %d (%.4fs)",
                rid,
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
            )
            return response
        finally:
            reset_request_id(token)
