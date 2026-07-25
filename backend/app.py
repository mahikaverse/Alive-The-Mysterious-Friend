"""FastAPI application factory.

Creates and configures the FastAPI application instance.
"""

from fastapi import FastAPI

from backend.api.routes import router
from backend.config.log_config import setup_logging
from backend.config.settings import settings


def create_app() -> FastAPI:
    """Create and return a configured FastAPI application."""
    setup_logging()

    app = FastAPI(
        title="Alive - The Mysterious Friend",
        description="A Human Simulation System for Masquerade '26 - The Turing Challenge",
        version="1.0.0",
    )

    app.include_router(router)

    return app
