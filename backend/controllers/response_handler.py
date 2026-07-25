"""Response handler.

Formats orchestrator output into the OpenAI-compatible
Chat Completions response schema.
"""

import logging
import time
import uuid

from backend.models.responses import ChatCompletionResponse, Choice, ResponseMessage

logger = logging.getLogger(__name__)


class ResponseHandler:
    """Formats internal responses into the OpenAI Chat Completions format."""

    def format_response(self, content: str, model: str) -> ChatCompletionResponse:
        """Wrap the generated content in an OpenAI-compatible response envelope."""
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=[
                Choice(
                    index=0,
                    message=ResponseMessage(role="assistant", content=content),
                    finish_reason="stop",
                )
            ],
        )

    def format_error(self, status_code: int, message: str) -> dict:
        """Return a standardised error response."""
        return {"error": message}
