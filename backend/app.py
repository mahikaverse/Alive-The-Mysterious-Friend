"""FastAPI application factory.

Creates and configures the FastAPI application instance
with middleware, exception handlers, lifecycle hooks,
and environment-aware setup.
"""

import logging
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import __app_name__, __description__, __version__
from backend.api.exceptions import (
    AppException,
    BadRequestException,
    InternalErrorException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
)
from backend.api.middleware import RequestContextMiddleware
from backend.api.routes import router
from backend.config.log_config import setup_logging
from backend.config.settings import settings, validate_settings
from backend.controllers.conversation_controller import ConversationController

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and return a configured FastAPI application."""
    setup_logging()

    app = FastAPI(
        title=__app_name__,
        description=__description__,
        version=__version__,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # --- middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)

    # --- singleton services ---
    app.state.orchestrator = ConversationController()
    app.state.start_time = __import__("time").time()

    # --- exception handlers ---
    @app.exception_handler(BadRequestException)
    async def bad_request_handler(request: Request, exc: BadRequestException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": exc.detail})

    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
        return JSONResponse(status_code=401, content={"error": exc.detail})

    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
        return JSONResponse(status_code=404, content={"error": exc.detail})

    @app.exception_handler(RateLimitException)
    async def rate_limit_handler(request: Request, exc: RateLimitException) -> JSONResponse:
        return JSONResponse(status_code=429, content={"error": exc.detail})

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning("App exception: %s", exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("Validation error: %s", exc)
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error."},
        )

    # --- lifecycle ---
    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info(
            "%s v%s starting — environment=%s",
            __app_name__,
            __version__,
            settings.environment,
        )
        missing = validate_settings()
        if missing:
            logger.warning("Missing recommended settings: %s", ", ".join(missing))
            if settings.is_production:
                logger.error(
                    "Required settings missing in production: %s. Application may not function correctly.",
                    ", ".join(missing),
                )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info(
            "%s v%s shutting down",
            __app_name__,
            __version__,
        )

    # --- routes ---
    app.include_router(router)

    return app
