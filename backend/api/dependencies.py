"""API dependency injection.

Provides shared dependencies for route handlers
such as database sessions and service instances.
"""

from fastapi import Request


def get_conversation_controller(request: Request):
    """Resolve the conversation controller from application state."""
    pass
