"""API dependency injection.

Provides shared dependencies for route handlers
such as the orchestrator, configuration, and request context.
"""

import logging

from fastapi import Request

from backend.config.settings import Settings, settings as app_settings
from backend.controllers.conversation_controller import ConversationController
from backend.utils.request_context import RequestContext, generate_request_id

logger = logging.getLogger(__name__)


def get_conversation_controller(request: Request) -> ConversationController:
    """Resolve the singleton ConversationController from application state."""
    controller: ConversationController = request.app.state.orchestrator
    return controller


def get_request_context(request: Request) -> RequestContext:
    """Build a RequestContext for the current request."""
    return RequestContext(
        request_id=request.state.request_id,
        start_time=request.state.start_time,
    )


def get_settings() -> Settings:
    """Return the application settings singleton."""
    return app_settings
