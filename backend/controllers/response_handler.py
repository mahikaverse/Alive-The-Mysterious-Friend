"""Response handler.

Formats orchestrator output into the OpenAI-compatible
Chat Completions response schema.
"""

import logging

logger = logging.getLogger(__name__)


class ResponseHandler:
    """Formats internal responses into the OpenAI Chat Completions format."""

    def format_response(self, content: str) -> dict:
        """Wrap the generated content in an OpenAI-compatible response envelope."""
        pass

    def format_error(self, status_code: int, message: str) -> dict:
        """Return a standardised error response."""
        pass

    def build_chunk(self, content: str) -> dict:
        """Build a streaming response chunk."""
        pass
