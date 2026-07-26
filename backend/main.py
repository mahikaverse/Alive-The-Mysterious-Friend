"""Application entry point.

Starts the FastAPI server using Uvicorn.
Configuration is loaded from environment variables via settings.
"""

import uvicorn

from backend.app import create_app
from backend.config.settings import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower() if settings.log_level else "info",
        timeout_graceful_shutdown=settings.shutdown_timeout,
    )
