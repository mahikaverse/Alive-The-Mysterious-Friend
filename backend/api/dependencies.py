"""API dependency injection.

Provides shared dependencies for route handlers
such as the orchestrator, configuration, and future service instances.

New services should be registered here and wired via FastAPI's
Depends() to keep route handlers clean and testable.
"""

import logging

from fastapi import Request

from backend.config.settings import Settings, settings as app_settings
from backend.controllers.conversation_controller import ConversationController

logger = logging.getLogger(__name__)


def get_conversation_controller(request: Request) -> ConversationController:
    """Resolve the singleton ConversationController from application state."""
    controller: ConversationController = request.app.state.orchestrator
    return controller


def get_settings() -> Settings:
    """Return the application settings singleton."""
    return app_settings
