"""FastAPI application factory.

Creates and configures the FastAPI application instance
with middleware, exception handlers, and router registration.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.middleware import RequestTimingMiddleware
from backend.api.routes import router
from backend.config.log_config import setup_logging
from backend.config.settings import settings
from backend.controllers.conversation_controller import ConversationController

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and return a configured FastAPI application."""
    setup_logging()

    app = FastAPI(
        title="Alive - The Mysterious Friend",
        description="A Human Simulation System for Masquerade '26 - The Turing Challenge",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestTimingMiddleware)

    app.state.orchestrator = ConversationController()

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error."},
        )

    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("Alive server starting")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("Alive server shutting down")

    app.include_router(router)

    return app
