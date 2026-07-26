"""API middleware.

Configures request context, timing, CORS, API key auth,
and metrics collection for the FastAPI application.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.api.exceptions import UnauthorizedException
from backend.config.settings import settings
from backend.utils.metrics import metrics_collector
from backend.utils.request_context import generate_request_id, set_request_id, reset_request_id

logger = logging.getLogger(__name__)

PUBLIC_PATHS: frozenset[str] = frozenset({
    "/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json",
})


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
            metrics_collector.record_request(request.url.path, response.status_code, elapsed)
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


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates API key on protected endpoints.

    If ``settings.api_key`` is empty, all requests pass through
    (no authentication required).  If set, every non-public endpoint
    must include ``Authorization: Bearer <key>``.
    """

    async def dispatch(self, request: Request, call_next):
        if not settings.api_key:
            return await call_next(request)

        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            rid = getattr(request.state, "request_id", "-")
            logger.warning("[%s] missing auth header on %s", rid, path)
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized."},
            )

        token = auth_header.removeprefix("Bearer ").strip()
        if token != settings.api_key:
            rid = getattr(request.state, "request_id", "-")
            logger.warning("[%s] invalid API key on %s", rid, path)
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized."},
            )

        return await call_next(request)
