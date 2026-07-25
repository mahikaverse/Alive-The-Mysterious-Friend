"""Request handler.

Parses, validates, and enriches incoming API requests
before delegating to the orchestrator.
"""

import logging

from backend.models.requests import ChatCompletionRequest, ConversationRequest

logger = logging.getLogger(__name__)


class RequestHandler:
    """Handles incoming request parsing and validation."""

    VALID_ROLES = {"system", "user", "assistant"}

    def parse(self, body: ChatCompletionRequest) -> ConversationRequest:
        """Parse a validated ChatCompletionRequest into an internal context."""
        if not body.messages:
            raise ValueError("messages list is empty")

        for msg in body.messages:
            if msg.role not in self.VALID_ROLES:
                raise ValueError(f"invalid role: {msg.role}")

        current = body.messages[-1].content if body.messages else ""

        return ConversationRequest(
            conversation=[m.model_dump() for m in body.messages],
            current_message=current,
            metadata={
                "model": body.model,
                "temperature": body.temperature,
                "max_tokens": body.max_tokens,
            },
        )
