"""API dependency injection.

Provides shared dependencies for route handlers
such as database sessions and service instances.
"""

from fastapi import Request

from backend.controllers.conversation_controller import ConversationController


def get_conversation_controller(request: Request) -> ConversationController:
    """Resolve the conversation controller from application state."""
    controller: ConversationController = request.app.state.orchestrator
    return controller
